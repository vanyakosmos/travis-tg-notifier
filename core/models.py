from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    photo_url = models.TextField(null=True, blank=True)
    auth_date = models.DateTimeField(null=True)
