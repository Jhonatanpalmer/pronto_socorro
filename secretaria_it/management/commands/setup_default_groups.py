from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

from secretaria_it.models import GroupAccess


GROUP_DEFINITIONS = {
    'Regulação': {'can_regulacao': True},
    'UBS': {'can_regulacao': True},
    'Gestão de Pacientes': {'can_pacientes': True},
    'Gestão de Viagens': {'can_viagens': True},
    'Gestão de TFD': {'can_tfd': True},
    'Veículos - Abastecimentos': {'can_veiculos': True},
    'RH': {'can_rh': True},
    'Motoristas': {'can_motorista': True},
}


class Command(BaseCommand):
    help = 'Garante a existência dos grupos padrão para cada módulo e aplica os acessos correspondentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        created = []
        updated = []

        for name, flags in GROUP_DEFINITIONS.items():
            group, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created.append(name)

            access, _ = GroupAccess.objects.get_or_create(group=group)
            changed = False
            for field_name, value in flags.items():
                if getattr(access, field_name) != value:
                    setattr(access, field_name, value)
                    changed = True
            if changed:
                access.save()
                updated.append(name)

        if created:
            self.stdout.write(self.style.SUCCESS(f'Grupos criados: {", ".join(created)}'))
        if updated:
            self.stdout.write(self.style.SUCCESS(f'Acessos atualizados: {", ".join(updated)}'))
        if not created and not updated:
            self.stdout.write('Grupos e acessos já estavam configurados.')
