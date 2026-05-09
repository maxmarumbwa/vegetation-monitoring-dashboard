from django.apps import AppConfig
import os


class EarthEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.earth_engine"

    def ready(self):
        # Prevent duplicate initialization in Django autoreloader
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .ee_config import initialize_earth_engine

        initialize_earth_engine()
