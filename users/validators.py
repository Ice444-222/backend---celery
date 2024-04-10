from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def special_names_validator(value):
    """
    Validator that checks usernames when user registrate
    """

    special_names = ['admin', 'staff', 'me', 'support', 'moderator']
    if value in special_names:
        raise ValidationError("Incorrect nickname for a user")


def email_validator(value):
    """
    Custom validator to check if the email address is in a real domain.
    """

    email_validator = EmailValidator()
    try:
        email_validator(value)
    except ValidationError as e:
        raise ValidationError('Invalid email format') from e
