import base64
import hashlib
import hmac
import json
from time import time
from unittest.mock import Mock

import pytest
import requests
from OpenSSL.crypto import (
    sign,
    load_privatekey,
    FILETYPE_PEM,
    TYPE_RSA,
    PKey,
    dump_privatekey,
    dump_publickey,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from telegram import Bot, Update, TelegramError
from telegram.error import BadRequest

import core.bot
import core.utils
from core.bot import command_start, command_webhook, bot, dispatcher
from core.utils import (
    get_tg_auth_payload,
    get_user,
    render_index,
    TravisSignatureChecker,
    send_report,
    validate_tg_auth_data,
    format_build_report,
    format_simple_report,
)

User = get_user_model()


def generate_keys():
    """
    Generate a new RSA key, return the PEM encoded public and private keys
    """
    pkey = PKey()
    pkey.generate_key(TYPE_RSA, 2048)
    public_key = dump_publickey(FILETYPE_PEM, pkey)
    private_key = dump_privatekey(FILETYPE_PEM, pkey)
    return public_key, private_key


def generate_signature(pem_private_key, content):
    """
    Given a private key and some content, generate a base64 encoded signature for that content.
    Use this during testing in combination with the public key to mimic the travis API.
    """
    private_key = load_privatekey(FILETYPE_PEM, pem_private_key)
    signature = sign(private_key, content, str('sha1'))
    return signature


def create_travis_payload():
    return json.dumps({
        'number': 13,
        'repository': {},
        'status_message': 'passed',
        'author_name': 'user',
        'duration': 13,
        'started_at': '2019-08-04T00:23:38Z',
        'finished_at': '2019-08-04T00:23:38Z',
        'committed_at': '2019-08-04T00:23:38Z',
        'build_url': 'example.com',
        'compare_url': 'example.com',
        'message': 'commit message',
    })


@pytest.mark.django_db
class TestUtils:
    def test_render_index(self):
        request = HttpRequest()
        res = render_index(request)
        assert isinstance(res, HttpResponse)
        assert 'usage' in res.content.decode().lower()

    def test_get_tg_auth_payload(self):
        s = get_tg_auth_payload({'a': '1', 'c': '2', 'b': '3'})
        assert s == 'a=1\nb=3\nc=2'

    def test_get_user_invalid(self):
        with pytest.raises(KeyError):
            get_user({})

    def test_get_user_new(self):
        assert User.objects.count() == 0
        u = get_user({'id': '1234', 'first_name': 'name'})
        assert User.objects.count() == 1
        assert u.first_name == 'name'

    def test_get_user(self):
        user = self.create_user(first_name='a')
        u = get_user({'id': user.username, 'first_name': 'b', 'auth_date': time()})
        assert u.id == user.id
        user.refresh_from_db()
        assert user.first_name == 'b'
        assert User.objects.count() == 1

    def test_validate_tg_auth_data_no_hash(self):
        assert not validate_tg_auth_data({})

    def test_verify_public_key(self):
        payload = '{"foo": "bar"}'
        pub, pri = generate_keys()
        signature = generate_signature(pri, payload)
        tsc = TravisSignatureChecker()
        assert tsc.validate_signature(signature, payload, pub)

    def test_verify_public_key_bad_sig(self):
        payload = '{"foo": "bar"}'
        pub, pri = generate_keys()
        tsc = TravisSignatureChecker()
        assert not tsc.validate_signature(b'bad_signature', payload, pub)

    def test_send_report(self, mocker):
        mocker.patch.object(TravisSignatureChecker, 'validate', return_value=True)
        req = HttpRequest()
        req.POST['payload'] = create_travis_payload()
        res = send_report(req, chat_id='1111')
        assert 'build' in res.content.decode().lower()
        assert res.status_code == 200

    def test_send_report_bad_sig(self, mocker):
        mocker.patch.object(TravisSignatureChecker, 'validate', return_value=False)
        req = HttpRequest()
        req.POST['payload'] = create_travis_payload()
        res = send_report(req, chat_id='1111')
        assert res.status_code == 400

    def test_send_report_with_simple(self, mocker):
        store = {'i': 0}  # or use global

        def send_msg(*args, **kwargs):
            print('send', store['i'])
            store['i'] += 1
            if store['i'] == 1:
                raise BadRequest("forced error")

        mocker.patch.object(Bot, 'send_message', send_msg)
        mocker.patch.object(TravisSignatureChecker, 'validate', return_value=True)
        mocker.spy(core.utils, 'format_simple_report')
        req = HttpRequest()
        req.POST['payload'] = create_travis_payload()
        res = send_report(req, chat_id='1111')
        assert res.status_code == 200
        assert core.utils.format_simple_report.call_count == 1

    def test_send_report_fail(self, mocker):
        mocker.patch.object(Bot, 'send_message', side_effect=BadRequest("force error"))
        mocker.patch.object(TravisSignatureChecker, 'validate', return_value=True)
        req = HttpRequest()
        req.POST['payload'] = create_travis_payload()
        res = send_report(req, chat_id='1111')
        assert res.status_code == 400

    def test_tsc_gen_public_key(self):
        tsc = TravisSignatureChecker()
        pubs = list(tsc.gen_public_key())
        assert len(pubs) == 2

    def test_tsc_gen_public_key_fail(self, mocker):
        mocker.patch.object(requests, 'get', side_effect=requests.RequestException('force error'))
        tsc = TravisSignatureChecker()
        pubs = list(tsc.gen_public_key())
        assert len(pubs) == 2
        assert all([p is None for p in pubs])

    def test_tsc_validation(self, mocker):
        payload = '{"foo": "bar"}'
        pub, pri = generate_keys()
        signature = generate_signature(pri, payload)
        tsc = TravisSignatureChecker()
        req = HttpRequest()
        req.POST['payload'] = payload
        req.META['HTTP_SIGNATURE'] = base64.b64encode(signature)
        mocker.patch.object(tsc, 'gen_public_key', return_value=[pub])
        assert tsc.validate(req)

    def test_tsc_validation_no_public_key(self, mocker):
        payload = '{"foo": "bar"}'
        pub, pri = generate_keys()
        signature = generate_signature(pri, payload)
        tsc = TravisSignatureChecker()
        req = HttpRequest()
        req.POST['payload'] = payload
        req.META['HTTP_SIGNATURE'] = base64.b64encode(signature)
        mocker.patch.object(tsc, 'gen_public_key', return_value=[None, None])
        assert not tsc.validate(req)


@pytest.mark.usefixtures('create_notification_payload')
class TestFormatReport:
    def test_basic(self):
        payload = self.create_notification_payload(status=0)
        res = format_build_report(payload)
        print(res)
        assert 'success' in res

    def test_error(self):
        payload = self.create_notification_payload(status=1)
        res = format_build_report(payload)
        print(res)
        assert 'failed' in res

    def test_multiline(self):
        payload = self.create_notification_payload(multiline_message=True)
        res = format_build_report(payload)
        print(res)

    def test_pull_request(self):
        payload = self.create_notification_payload(pull_request=True)
        res = format_build_report(payload)
        assert 'pull request' in res.lower()
        print(res)

    def test_simple(self):
        res = format_simple_report({
            'repository': {},
            'number': 13,
            'status_message': 'Passed',
            'author_name': 'user',
            'message': 'commit',
            'duration': 10,
        })
        res = res.strip('`\n')
        # check that there is valid objects
        assert json.loads(res)


@pytest.mark.django_db
class TestViews:
    def test_index_view(self):
        url = reverse('core:index')
        res = self.client.get(url)
        assert 'usage' in res.content.decode().lower()

    def test_index_view_auth(self):
        user = self.create_user()
        self.client.force_login(user)
        url = reverse('core:index')
        res = self.client.get(url)
        assert res.status_code == 302

    def test_login_success_view_bad_hash(self):
        url = reverse('core:login_success')
        res = self.client.get(url, {'hash': 'foo', 'id': '1234'})
        assert res.status_code == 400

    def test_login_success_view(self):
        data = {'id': '1234', 'first_name': 'name'}
        payload = get_tg_auth_payload(data)
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        hash = hmac.new(secret_key, payload.encode(), digestmod=hashlib.sha256).hexdigest()

        assert User.objects.count() == 0

        url = reverse('core:login_success')
        res = self.client.get(url, {'hash': hash, **data}, follow=True)
        assert res.status_code == 200
        assert User.objects.get(username=data['id'])

    def test_user_hook_view_404(self):
        url = reverse('core:user', kwargs={'user_id': '1234'})
        res = self.client.get(url)
        assert res.status_code == 404

    def test_user_hook_view_another_user(self):
        self.create_user(username='1234')

        url = reverse('core:user', kwargs={'user_id': '1234'})
        res = self.client.get(url)
        assert res.status_code == 302

        user = self.create_user(username='4321')
        self.client.force_login(user)
        url = reverse('core:user', kwargs={'user_id': '1234'})
        res = self.client.get(url)
        assert res.status_code == 302

    def test_user_hook_view_self(self):
        user = self.create_user(username='1234')
        self.client.force_login(user)
        url = reverse('core:user', kwargs={'user_id': '1234'})
        res = self.client.get(url)
        assert res.status_code == 200

    def test_user_hook_view_report_no_payload(self):
        user = self.create_user(username='1234')
        self.client.force_login(user)
        url = reverse('core:user', kwargs={'user_id': '1234'})
        res = self.client.post(url)
        assert res.status_code == 400

    def test_user_forced_hook_view(self):
        url = reverse('core:forced', kwargs={'chat_id': '1234'})
        res = self.client.get(url, follow=True)
        assert res.status_code == 200
        assert res.redirect_chain[-1][0] == reverse('core:index')

    def test_user_forced_hook_view_self(self):
        user = self.create_user(username='1234')
        self.client.force_login(user)
        url = reverse('core:forced', kwargs={'chat_id': '1234'})
        res = self.client.get(url, follow=True)
        assert res.status_code == 200
        assert res.redirect_chain[-1][0] == reverse('core:user', kwargs={'user_id': '1234'})

    def test_user_forced_hook_view_report(self, mocker):
        mocker.patch.object(TravisSignatureChecker, 'validate', return_value=True)
        url = reverse('core:forced', kwargs={'chat_id': '1234'})
        res = self.client.post(url, data={'payload': create_travis_payload()})
        assert res.status_code == 200

    def test_logout_view_anon(self):
        url = reverse('core:logout')
        res = self.client.get(url, follow=True)
        assert res.status_code == 200
        assert res.redirect_chain[-1][0] == reverse('core:index')

    def test_logout_view(self):
        user = self.create_user(username='1234')
        self.client.force_login(user)

        url = reverse('core:logout')
        res = self.client.get(url, follow=True)
        assert res.status_code == 200

        user.refresh_from_db()
        assert not user.is_active

    def test_logout_view_staff(self):
        user = self.create_user(username='1234', is_staff=True)
        self.client.force_login(user)

        url = reverse('core:logout')
        res = self.client.get(url, follow=True)
        assert res.status_code == 200

        user.refresh_from_db()
        assert user.is_active

    def test_bot_webhook_view_404(self):
        url = reverse('core:webhook')
        res = self.client.get(url)
        assert res.status_code == 404

    def test_bot_webhook_view(self):
        url = reverse('core:webhook')
        res = self.client.post(url, {'update_id': '1234'}, content_type='application/json')
        assert res.status_code == 200


class TestBot:
    def create_update(self, text=None, command=None):
        return Update.de_json(
            {
                "update_id": 111111111,
                "message": {
                    "message_id": 111111,
                    "from": {
                        "id": 111111111,
                        "is_bot": False,
                        "first_name": "user",
                    },
                    "chat": {
                        "id": 111111111,
                        "first_name": "user",
                        "type": "private"
                    },
                    "date": 1565092779,
                    "text": command if command else text,
                    "entities": [{
                        "offset": 0,
                        "length": len(command),
                        "type": "bot_command"
                    }] if command else None
                }
            },
            bot,
        )

    def test_command_start(self, mocker):
        mocker.patch.object(Bot, 'send_message')
        mocker.spy(Bot, 'send_message')
        command_start(Mock(), Mock())
        assert Bot.send_message.call_count == 1

    def test_command_webhook(self, mocker):
        mocker.patch.object(Bot, 'send_message')
        mocker.spy(Bot, 'send_message')
        update = self.create_update('foo')
        command_webhook(update, Mock())
        assert settings.APP_URL in Bot.send_message.call_args[0][1]

    def test_error(self, mocker):
        mocker.patch.object(Bot, 'send_message', side_effect=TelegramError('error'))
        mocker.spy(Bot, 'send_message')
        mocker.spy(core.bot.logger, 'error')
        update = self.create_update(command='/start')
        dispatcher.process_update(update)
        assert Bot.send_message.call_count == 1
        assert core.bot.logger.error.call_count == 2
