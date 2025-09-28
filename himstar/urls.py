"""
URL configuration for himstar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from .views import main_page, contact_us, payment_page, privacy_page, terms_page, withdraw_page
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Himstar API",
        default_version='v1',
        description="API documentation for Himstar Backend",
        terms_of_service="https://himstars.com/terms/",
        contact=openapi.Contact(email="support@himstars.com"),
        license=openapi.License(name="Private License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_page, name='main_page'),
    path('contact/', contact_us, name='contact_us'),
    path('payment/', payment_page, name='payment_page'),
    path('privacy-policy/', privacy_page, name='privacy_page'),
    path('terms/', terms_page, name='terms_page'),
    path('withdrawl/', withdraw_page, name='withdraw_page'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/', include('accounts.urls')),
    path('api/', include('banners.urls')),
    path('api/', include('dashboard.urls')),
    path('api/', include('video.urls')),
    path('api/', include('levels.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('contact.urls')),
    path('api/', include('wallet.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
