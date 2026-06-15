"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Ensure media directory exists on startup
BASE_DIR = Path(__file__).resolve().parent.parent
(BASE_DIR / 'media').mkdir(exist_ok=True)

application = get_wsgi_application()
