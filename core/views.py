import logging

from django.contrib.auth import get_user_model, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from telegram import ParseMode

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
    return redirect('core:user', user_id=user.username)


def user_hook_view(request: HttpRequest, user_id: str):
    if request.method == 'POST':
        user = get_object_or_404(User, username=user_id, is_active=True)
        if not verify_public_key(request):
            return HttpResponse('bad signature', status=400)
        text = format_build_report({})
        bot.send_message(chat_id=user.username, text=text, parse_mode=ParseMode.MARKDOWN)
        return HttpResponse('ok')
    return render_index(request)


def logout_view(request: HttpRequest):
    u = request.user
    if u.is_authenticated:
        u.is_active = False
        u.save()
    logout(request)
    return redirect('core:index')
