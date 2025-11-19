from django.db import models
from django.contrib.auth.models import Group


class GroupAccess(models.Model):
    """Access flags per Django Group to control which modules a group can use."""

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="access")

    # High-level module access flags
    can_pacientes = models.BooleanField(default=False, verbose_name="Pacientes")
    can_viagens = models.BooleanField(default=False, verbose_name="Viagens")
    can_tfd = models.BooleanField(default=False, verbose_name="TFD")
    can_regulacao = models.BooleanField(default=False, verbose_name="Regulação")
    can_users_admin = models.BooleanField(
        default=False, verbose_name="Administração de Usuários/Grupos"
    )
    can_motorista = models.BooleanField(default=False, verbose_name="Motoristas")
    can_rh = models.BooleanField(default=False, verbose_name="Recursos Humanos")
    can_veiculos = models.BooleanField(default=False, verbose_name="Veículos / Abastecimentos")

    class Meta:
        verbose_name = "Acesso do Grupo"
        verbose_name_plural = "Acessos dos Grupos"

    def __str__(self) -> str:  # pragma: no cover
        return f"Acessos: {self.group.name}"
