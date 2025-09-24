from django.apps import AppConfig


class FuncionariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'funcionarios'

    def ready(self):  # pragma: no cover
        # Ensure signals for GroupAccess are registered
        try:
            import secretaria_it.signals  # noqa: F401
        except Exception:
            # Avoid crashing app boot if optional signals not available
            pass
