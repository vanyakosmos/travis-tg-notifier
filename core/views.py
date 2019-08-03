import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from telegram import ParseMode
from telegram.error import BadRequest

from core.bot import bot
from core.utils import (
    render_index,
    validate_data,
    get_user,
    verify_public_key,
    format_build_report,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def index_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('core:user', user_id=request.user.username)
    return render_index(request)


def login_success_view(request):
    data = {key: value for key, value in request.GET.items()}
    if not validate_data(data):
        return HttpResponse("invalid hash", status=400)

    user = get_user(data)
    login(request, user)
    bot.send_message(chat_id=user.username, text=f"Successfully signed in on {settings.APP_URL}.")
    return redirect('core:user', user_id=user.username)


@csrf_exempt
def user_hook_view(request: HttpRequest, user_id: str):
    if request.method == 'POST':
        user = get_object_or_404(User, username=user_id, is_active=True)
        if not verify_public_key(request):
            return HttpResponse('bad signature', status=400)
        text = format_build_report({})
        try:
            bot.send_message(chat_id=user.username, text=text, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e:
            return HttpResponse(str(e), status=400)
        return HttpResponse('ok')
    return render_index(request)


@csrf_exempt
def user_forced_hook_view(request: HttpRequest, chat_id: str):
    if request.method == 'POST':
        if 'payload' not in request.GET:
            return HttpResponse('not payload', status=400)
        if not verify_public_key(request):
            return HttpResponse('bad signature', status=400)

        data = json.loads(request.GET['payload'])
        text = format_build_report(data)
        try:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except BadRequest as e:
            return HttpResponse(str(e), status=400)
        return HttpResponse(text, 'text/html')
    return redirect('core:index')


def logout_view(request: HttpRequest):
    user = request.user
    if user.is_authenticated:
        user.is_active = False
        user.save()
    logout(request)
    return redirect('core:index')
