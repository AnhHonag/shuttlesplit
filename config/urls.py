from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('groups.urls')),
    path('', include('sessions_app.urls')),
    path('', include('payments.urls')),
    path('', include('wallet.urls')),
    path('', include('meals.urls')),
    # Serve uploaded media files in all environments (avatars, QR codes, receipts, covers)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
