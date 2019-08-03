import hashlib
import hmac
from datetime import datetime

from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from markdown import markdown

User = get_user_model()


def render_index(request):
    with open('README.md', 'r') as f:
        readme = markdown(f.read(), extensions=['fenced_code'])
    readme = mark_safe(readme)
    return render(request, 'index.html', context={'readme': readme})


def index_view(request: HttpRequest):
    return render_index(request)


def validate_data(data: dict):
    if 'hash' not in data:
        return False
    valid_hash = data.pop('hash')
    string = '\n'.join(map(
        lambda e: f"{e}={data[e]}",
        sorted(data),
    ))
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    hash = hmac.new(secret_key, string.encode(), digestmod=hashlib.sha256).hexdigest()
    return valid_hash == hash


def get_user(data: dict):
    user = User.objects.filter(username=data['id']).first()
    if not user:
        user = User.objects.create_user(
            username=data['id'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name', ''),
            photo_url=data.get('photo_url'),
            auth_date=datetime.fromtimestamp(int(data['auth_date']))
        )
    user.is_active = True
    user.save()
    return user


def login_success_view(request):
    data = {key: value for key, value in request.GET.items()}
    valid = validate_data(data)
    if not valid:
        return HttpResponse("invalid hash", status=400)

    user = get_user(data)
    login(request, user)
    return redirect('core:user', user_id=user.username)


def user_hook_view(request: HttpRequest, user_id: str):
    if request.method == 'POST':
        user = get_object_or_404(User, username=user_id, is_active=True)
        print(user)
        # todo: verify public key
        # send status to user
        return HttpResponse('ok')
    return render_index(request)


def logout_view(request):
    u = request.user
    if isinstance(u, User):
        u.is_active = False
        u.save()
    logout(request)
    return redirect('core:index')
