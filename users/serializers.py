from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import OneTimePassword

User = get_user_model()


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer for obtaining authentication tokens with email,
    password, and OTP.
    """
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    otp = serializers.CharField(write_only=True)

    class Meta:
        fields = ['email', 'password', 'otp']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        otp = attrs.get("otp")

        if email and password and otp:
            try:
                user = User.objects.get(email=email)
                if not user.verified:
                    raise serializers.ValidationError(
                        "Your email is not verified yet."
                    )
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "User with this email does not exist."
                )
            if not authenticate(email=email, password=password):
                raise serializers.ValidationError("Incorrect password.")
            try:
                otp_instance = OneTimePassword.objects.get(user=user, otp=otp)
                if not otp_instance.is_otp_valid():
                    raise serializers.ValidationError("OTP is expired.")
                if user.otp_tries > 5:
                    raise serializers.ValidationError(
                        "Exceeded maximum attempts to enter OTP."
                    )
            except OneTimePassword.DoesNotExist:
                user.otp_tries += 1
                user.save()
                raise serializers.ValidationError("Invalid OTP.")
        else:
            raise serializers.ValidationError(
                "Email, password, and OTP must be provided."
            )
        user.otp_tries = 0
        user.save()
        otp_instance.delete()
        attrs["user"] = user
        return attrs
