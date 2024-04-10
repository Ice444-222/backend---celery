from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, get_otp, verify_account

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")


urlpatterns = [
    path("", include(router.urls)),
    path('verify/', verify_account, name='verify_account'),
    path('otp/', get_otp, name='one_time_password'),
]
