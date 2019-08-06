import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime

import dateutil.parser
import requests
from OpenSSL.crypto import verify, load_publickey, FILETYPE_PEM, X509
from OpenSSL.crypto import Error as SignatureError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from markdown import markdown
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
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


def get_tg_auth_payload(data: dict):
    return '\n'.join(map(
        lambda e: f"{e}={data[e]}",
        sorted(data),
    ))


def validate_tg_auth_data(data: dict):
    if 'hash' not in data:
        return False
    valid_hash = data.pop('hash')
    payload = get_tg_auth_payload(data)
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    hash = hmac.new(secret_key, payload.encode(), digestmod=hashlib.sha256).hexdigest()
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


def format_build_report(data: dict):
    for field in ['started_at', 'finished_at', 'committed_at']:
        data[field] = dateutil.parser.parse(data[field])
    data['multiline'] = '\n' in data['message']
    data['message'] = mark_safe(data['message'])
    return render_to_string('report.html', context=data)


def format_simple_report(data: dict):
    sub = {}
    for key in ['repository', 'number', 'status_message', 'author_name', 'message', 'duration']:
        sub[key] = data[key]
    text = json.dumps(sub, indent=2, ensure_ascii=False)
    return f'```\n{text}\n```'


def send_report(request: HttpRequest, chat_id):
    if 'payload' not in request.POST:
        return HttpResponse('no payload', status=400)

    tsc = TravisSignatureChecker()
    if settings.CHECK_SIGNATURE and not tsc.validate(request):
        return HttpResponse('bad signature', status=400)

    data = json.loads(request.POST['payload'])
    text = format_build_report(data)
    try:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup.from_row([
                InlineKeyboardButton('details', url=data['build_url']),
                InlineKeyboardButton('diff', url=data['compare_url']),
            ])
        )
    except BadRequest:
        pass
    else:
        return HttpResponse(text, 'text/markdown')

    try:
        text = format_simple_report(data)
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup.from_row([
                InlineKeyboardButton('details', url=data['build_url']),
                InlineKeyboardButton('diff', url=data['compare_url']),
            ])
        )
    except BadRequest as e:
        return HttpResponse(str(e), status=400)
    return HttpResponse(text, 'text/markdown')


class TravisSignatureChecker:
    def validate(self, request: HttpRequest) -> bool:
        signature = self.get_signature(request)
        payload = request.POST['payload']
        for public_key in self.gen_public_key():
            if not public_key:
                continue
            return self.validate_signature(signature, payload, public_key)
        logger.debug("problem with fetching public keys")
        return False

    def validate_signature(self, signature, payload, public_key):
        try:
            self.check_authorized(signature, public_key, payload)
            return True
        except SignatureError as e:
            logger.debug(f"invalid signature: {e}")
            return False

    def check_authorized(self, signature, public_key, payload):
        """
        Convert the PEM encoded public key to a format palatable for pyOpenSSL,
        then verify the signature
        """
        pkey_public_key = load_publickey(FILETYPE_PEM, public_key)
        certificate = X509()
        certificate.set_pubkey(pkey_public_key)
        verify(certificate, signature, payload, 'sha1')

    def get_signature(self, request):
        """
        Extract the raw bytes of the request signature provided by travis
        """
        signature = request.META['HTTP_SIGNATURE']
        return base64.b64decode(signature)

    def gen_public_key(self):
        """
        Fetch public key for public and private repos.
        """
        for url in ['https://api.travis-ci.org/config', 'https://api.travis-ci.com/config']:
            try:
                response = requests.get(url, timeout=10.0)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.debug(e)
                yield None
            else:
                yield response.json()['config']['notifications']['webhook']['public_key']
