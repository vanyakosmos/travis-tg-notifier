import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

from core.utils import render_index, get_message, get_user

User = get_user_model()


@pytest.mark.usefixtures('create_user')
@pytest.mark.django_db
class TestUtils:
    def test_render_index(self):
        request = HttpRequest()
        res = render_index(request)
        assert isinstance(res, HttpResponse)
        assert 'usage' in res.content.decode().lower()

    def test_get_message(self):
        s = get_message({'a': '1', 'c': '2', 'b': '3'})
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
        u = get_user({'id': user.username, 'first_name': 'b'})
        assert u.id == user.id
        user.refresh_from_db()
        assert user.first_name == 'b'
        assert User.objects.count() == 1
