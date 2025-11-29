from django.apps import AppConfig


class ResticConfig(AppConfig):
    """Присваивание пути приложения"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "restic"

    def ready(self):
        import restic.signals  # noqa: F401
