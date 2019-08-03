import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from core.bot import bot
from core.utils import get_user, render_index, send_report, validate_data

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
        return send_report(request, user.username)
    return render_index(request)


@csrf_exempt
def user_forced_hook_view(request: HttpRequest, chat_id: str):
    if request.method == 'POST':
        return send_report(request, chat_id)
    return redirect('core:index')


def logout_view(request: HttpRequest):
    user = request.user
    if user.is_authenticated:
        user.is_active = False
        user.save()
    logout(request)
    return redirect('core:index')
