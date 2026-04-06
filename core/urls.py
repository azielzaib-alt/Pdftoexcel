from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('converter.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
