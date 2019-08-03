import uuid
from typing import Callable

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


@pytest.fixture(scope='class')
def create_user(request: FixtureRequest):
    def _factory(**kwargs):
        fields = {
            'username': get_id(),
            **kwargs,
        }
        user = User.objects.create_user(**fields)
        return user

    return append_to_cls(request, _factory, 'create_user')
