import json
import uuid
from typing import Callable

from telegram import User as TGUser, Bot
import pytest
from _pytest.fixtures import FixtureRequest
from django.contrib.auth import get_user_model

User = get_user_model()


def get_id():
    # generate 128 bit number and shift it by 64
    return str(uuid.uuid1().int >> 64)


def append_to_cls(request: FixtureRequest, func: Callable, name: str = None):
    name = name or func.__name__.strip('_')
    setattr(request.cls, name, staticmethod(func))
    return func


@pytest.fixture(scope='class', autouse=True)
def create_user(request: FixtureRequest):
    def _factory(**kwargs):
        fields = {
            'username': get_id(),
            **kwargs,
        }
        user = User.objects.create_user(**fields)
        return user

    return append_to_cls(request, _factory, 'create_user')


@pytest.fixture(autouse=True)
def mock_bot(mocker):
    def get_me(self):
        self.bot = TGUser(id='1234', first_name='bot_name', username='test_bot', is_bot=True)
        return self.bot

    mocker.patch.object(Bot, 'get_me', get_me)
    mocker.patch.object(Bot, 'send_message')


@pytest.fixture(autouse=True)
def auto_client(request: FixtureRequest, client):
    return append_to_cls(request, client, 'client')


@pytest.fixture(scope='class')
def create_notification_payload(request):
    def _factory(status=1, pull_request=False, multiline_message=False):
        data = '{"id":568301538,"number":"619","config":{"os":"linux","dist":"trusty","sudo":false,"cache":{"pip":true,"directories":["vendor/bundle","node_modules"]},"group":"stable","deploy":{"app":"docs-travis-ci-com","true":{"branch":["master"]},"api_key":{"secure":"hylw2GIHMvZKOKX3uPSaLEzVrUGEA9mzGEA0s4zK37W9HJCTnvAcmgRCwOkRuC4L7R4Zshdh/CGORNnBBgh1xx5JGYwkdnqtjHuUQmWEXCusrIURu/iEBNSsZZEPK7zBuwqMHj2yRm64JfbTDJsku3xdoA5Z8XJG5AMJGKLFgUQ="},"provider":"heroku","skip_cleanup":true},"python":["3.5.2"],"script":["bundle exec rake test"],".result":"configured","install":["rvm use 2.3.1 --install","bundle install --deployment"],"branches":{"only":["master"]},"language":"python","global_env":["PATH=$HOME/.local/user/bin:$PATH"],"notifications":{"slack":{"rooms":{"secure":"LPNgf0Ra6Vu6I7XuK7tcnyFWJg+becx1RfAR35feWK81sru8TyuldQIt7uAKMA8tqFTP8j1Af7iz7UDokbCCfDNCX1GxdAWgXs+UKpwhO89nsidHAsCkW2lWSEM0E3xtOJDyNFoauiHxBKGKUsApJTnf39H+EW9tWrqN5W2sZg8="},"on_success":"never"},"webhooks":"https://docs.travis-ci.com/update_webhook_payload_doc"}},"type":"cron","state":"failed","status":1,"result":1,"status_message":"Still Failing","result_message":"Still Failing","started_at":"2019-08-06T10:36:13Z","finished_at":"2019-08-06T10:38:11Z","duration":118,"build_url":"https://travis-ci.org/lapolinar/docs-travis-ci-com/builds/568301538","commit_id":171901043,"commit":"14e8e737d1054b1776bb7b9c2ddfa793f2f85cfa","base_commit":null,"head_commit":null,"branch":"master","message":"Update deployments.yml","compare_url":"https://github.com/lapolinar/docs-travis-ci-com/compare/33860b3691f30239349f6fd245a97aaebeae102c...14e8e737d1054b1776bb7b9c2ddfa793f2f85cfa","committed_at":"2019-01-06T02:01:09Z","author_name":"apolinar","author_email":"lapolinar2368@gmail.com","committer_name":"GitHub","committer_email":"noreply@github.com","pull_request":false,"pull_request_number":null,"pull_request_title":null,"tag":null,"repository":{"id":15948437,"name":"docs-travis-ci-com","owner_name":"lapolinar","url":null},"matrix":[{"id":568301539,"repository_id":15948437,"parent_id":568301538,"number":"619.1","state":"failed","config":{"os":"linux","dist":"trusty","sudo":false,"cache":{"pip":true,"directories":["vendor/bundle","node_modules"]},"group":"stable","addons":{"deploy":{"app":"docs-travis-ci-com","true":{"branch":["master"]},"api_key":{"secure":"hylw2GIHMvZKOKX3uPSaLEzVrUGEA9mzGEA0s4zK37W9HJCTnvAcmgRCwOkRuC4L7R4Zshdh/CGORNnBBgh1xx5JGYwkdnqtjHuUQmWEXCusrIURu/iEBNSsZZEPK7zBuwqMHj2yRm64JfbTDJsku3xdoA5Z8XJG5AMJGKLFgUQ="},"provider":"heroku","skip_cleanup":true}},"python":"3.5.2","script":["bundle exec rake test"],".result":"configured","install":["rvm use 2.3.1 --install","bundle install --deployment"],"branches":{"only":["master"]},"language":"python","global_env":["PATH=$HOME/.local/user/bin:$PATH"],"notifications":{"slack":{"rooms":{"secure":"LPNgf0Ra6Vu6I7XuK7tcnyFWJg+becx1RfAR35feWK81sru8TyuldQIt7uAKMA8tqFTP8j1Af7iz7UDokbCCfDNCX1GxdAWgXs+UKpwhO89nsidHAsCkW2lWSEM0E3xtOJDyNFoauiHxBKGKUsApJTnf39H+EW9tWrqN5W2sZg8="},"on_success":"never"},"webhooks":"https://docs.travis-ci.com/update_webhook_payload_doc"}},"status":1,"result":1,"commit":"14e8e737d1054b1776bb7b9c2ddfa793f2f85cfa","branch":"master","message":"Update deployments.yml","compare_url":"https://github.com/lapolinar/docs-travis-ci-com/compare/33860b3691f30239349f6fd245a97aaebeae102c...14e8e737d1054b1776bb7b9c2ddfa793f2f85cfa","started_at":"2019-08-06T10:36:13Z","finished_at":"2019-08-06T10:38:11Z","committed_at":"2019-01-06T02:01:09Z","author_name":"apolinar","author_email":"lapolinar2368@gmail.com","committer_name":"GitHub","committer_email":"noreply@github.com","allow_failure":false}]}'
        payload = json.loads(data)

        payload['status'] = status
        payload['result'] = status

        if pull_request:
            payload['branch'] = 'feature'
            payload['pull_request'] = True
            payload['pull_request_number'] = 13
            payload['pull_request_title'] = 'pull request title'

        payload['multiline'] = '\n' in payload['message']
        if multiline_message:
            payload['message'] = (
                'commit message\n\n'
                'some info [and url](https://example.com)\n'
                '<noreply@example.com>'
            )

        return payload

    return append_to_cls(request, _factory, 'create_notification_payload')
