import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

from core.utils import _verify_public_key, get_message, get_user, render_index

User = get_user_model()


@pytest.mark.usefixtures('create_user', 'mock_bot')
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

    def test_verify_public_key(self):
        payload = b'json payload'
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        signature = private_key.sign(
            payload,
            padding.PSS(mgf=padding.MGF1(hashes.SHA1()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        public_key = private_key.public_key()
        pub = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        assert _verify_public_key(signature, payload, pub)
        assert not _verify_public_key(signature + b'a', payload, pub)
