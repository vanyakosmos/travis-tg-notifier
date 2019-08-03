import pytest
from OpenSSL.crypto import (
    sign,
    load_privatekey,
    FILETYPE_PEM,
    TYPE_RSA,
    PKey,
    dump_privatekey,
    dump_publickey,
)
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

from core.utils import get_tg_auth_payload, get_user, render_index, TravisSignatureChecker

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


@pytest.mark.usefixtures('create_user', 'mock_bot')
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
        u = get_user({'id': user.username, 'first_name': 'b'})
        assert u.id == user.id
        user.refresh_from_db()
        assert user.first_name == 'b'
        assert User.objects.count() == 1

    def test_verify_public_key(self):
        payload = '{"foo": "bar"}'
        pub, pri = generate_keys()
        signature = generate_signature(pri, payload)
        tsc = TravisSignatureChecker()
        assert tsc.validate_signature(signature, payload, pub)
