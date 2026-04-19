from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('django.contrib.auth.urls')),  # gives password_reset, password_change etc.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
