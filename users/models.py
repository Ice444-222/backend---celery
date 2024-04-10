import random

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .validators import special_names_validator


class User(AbstractUser):
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                r"^[\w.@+-]+\Z",
                "Only letters, numbers and special symbols"
                " @/./+/-/_ allowed in nickname",
            ),
            special_names_validator,
        ],
    )
    email = models.EmailField(
        max_length=254, unique=True,
    )
    first_name = models.CharField(
        max_length=150, verbose_name="First name",
    )
    last_name = models.CharField(
        max_length=150, verbose_name="Last name",
    )
    verified = models.BooleanField(default=False)
    otp_tries = models.IntegerField(
        default=0, verbose_name="Attempts to verificate or log in"
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    extra_kwargs = {
            'password': {'write_only': True},
        }

    def __str__(self):
        return self.username

    def generate_otp(self,):
        """
        Generates a 6-digit one-time password (OTP) and stores it for the user.
        """
        otp_instance, created = OneTimePassword.objects.update_or_create(
            user=self,
            defaults={
                'otp': ''.join([str(random.randint(0, 9)) for _ in range(6)]),
                'otp_expiration': (
                    timezone.now() + timezone.timedelta(minutes=15)
                )
            }
        )
        self.otp_tries = 0
        self.save()
        return otp_instance.otp


class OneTimePassword(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='otp'
    )
    otp = models.CharField(max_length=6, verbose_name="One time password")
    otp_expiration = models.DateTimeField(verbose_name="Expiration datetime")

    def is_otp_valid(self):
        return timezone.now() < self.otp_expiration
