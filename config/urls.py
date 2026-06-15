from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('groups.urls')),
    path('', include('sessions_app.urls')),
    path('', include('payments.urls')),
    path('', include('wallet.urls')),
]

# Always serve media files (user uploads: avatars, QR codes, receipts)
# WhiteNoise handles static files in production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
