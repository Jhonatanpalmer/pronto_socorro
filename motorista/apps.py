from django.apps import AppConfig


class MotoristaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'motorista'

    def ready(self):  # pragma: no cover
        try:
            import secretaria_it.signals  # noqa: F401
        except Exception:
            pass
