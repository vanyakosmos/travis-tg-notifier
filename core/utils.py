import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from markdown import markdown
from telegram import ParseMode
from telegram.error import BadRequest

from core.bot import bot

logger = logging.getLogger(__name__)
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


def _verify_public_key(signature: bytes, payload: bytes, public_key: bytes):
    public_key = load_pem_public_key(public_key, default_backend())
    try:
        public_key.verify(
            signature,
            payload,
            padding.PSS(mgf=padding.MGF1(hashes.SHA1()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def get_public_key():
    data = requests.get('https://api.travis-ci.com/config').json()
    public_key = data['config']['notifications']['webhook']['public_key']
    return public_key


def verify_public_key(request: HttpRequest):
    logger.info(request.META)
    if 'SIGNATURE' not in request.META:
        return False
    signature = base64.b64decode(request.META['SIGNATURE'].encode())
    logger.debug(f'signature: {signature}')

    payload = request.GET['payload']
    logger.debug(f'payload: {payload[:100]}...')

    public_key = get_public_key()
    logger.debug(f'public_key: {public_key}')
    valid = _verify_public_key(
        signature,
        payload.encode(),
        public_key.encode(),
    )
    logger.info(f"VALID: {valid}")
    return True  # fixme


def format_build_report(data: dict):
    logger.info(data)
    # for field in ['started_at', 'finished_at', 'committed_at']:
    #     data[field] = datetime.strptime(data[field], "%Y-%m-%dT%H:%M:%S%z")
    return render_to_string('report.html', context=data)  # fixme


def validate(request: HttpRequest):
    if 'payload' not in request.GET:
        return HttpResponse('not payload', status=400)
    if not verify_public_key(request):
        return HttpResponse('bad signature', status=400)


def send_report(request: HttpRequest, chat_id):
    resp = validate(request)
    if resp:
        return resp

    data = json.loads(request.GET['payload'])
    text = format_build_report(data)
    try:
        bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
    except BadRequest as e:
        return HttpResponse(str(e), status=400)
    return HttpResponse(text, 'text/html')
