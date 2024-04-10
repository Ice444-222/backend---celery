import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task
def send_otp_email_celery(email, otp):
    message = f'Your OTP is: {otp}'
    send_mail(
        'Lengevity inTime login', message,
        settings.EMAIL_HOST, [email], fail_silently=True
        )
