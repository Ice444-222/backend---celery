from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static

from users import views

schema_view = get_schema_view(
    openapi.Info(
        title="Longevity-InTime API",
        default_version='v1',
        description=(
            "This documentation contains information "
            "about users model endpoints and tokens."
        ),
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="turnpace1000@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path(
        'swagger/', schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
    path(
        'redoc/', schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
    path('admin/', admin.site.urls),
    path("api/", include("api.urls")),
    path(
        "auth/token/login/", views.CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "auth/token/logout/", views.TokenLogoutView.as_view(),
        name='token_logout'
    ),
]


