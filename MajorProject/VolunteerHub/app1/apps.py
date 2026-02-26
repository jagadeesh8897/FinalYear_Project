# apps.py

from django.apps import AppConfig
import os


class App1Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app1'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from . import scheduler
            scheduler.start()