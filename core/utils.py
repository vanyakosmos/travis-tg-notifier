import hashlib
import hmac
import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.safestring import mark_safe
from markdown import markdown

from core.bot import bot

User = get_user_model()


def render_index(request, **extra_context):
    with open('README.md', 'r') as f:
        readme = markdown(f.read(), extensions=['fenced_code'])
    readme = mark_safe(readme)
    return render(
        request,
        'index.html',
        context={
            'readme': readme,
            'bot_username': bot.username,
            **extra_context,
        }
    )


def get_message(data: dict):
    return '\n'.join(map(
        lambda e: f"{e}={data[e]}",
        sorted(data),
    ))


def validate_data(data: dict):
    if 'hash' not in data:
        return False
    valid_hash = data.pop('hash')
    string = get_message(data)
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    hash = hmac.new(secret_key, string.encode(), digestmod=hashlib.sha256).hexdigest()
    return valid_hash == hash


def get_user(data: dict):
    # can't user update_or_create because user must be create with specific method
    defaults = {
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name', ''),
        'photo_url': data.get('photo_url'),
        'is_active': True,
    }
    if 'auth_date' in data:
        defaults['auth_date'] = datetime.fromtimestamp(int(data['auth_date']))
    try:
        user = User.objects.get(username=data['id'])
        for key, value in defaults.items():
            setattr(user, key, value)
        user.save()
    except User.DoesNotExist:
        user = User.objects.create_user(username=data['id'], **defaults)
    return user


def verify_public_key(request: HttpRequest):
    # todo
    # requests.get('https://api.travis...')
    return True


def format_build_report(data: dict):
    # todo
    report = json.dumps(data, indent=2)
    return f'```report:\n{report}```'
