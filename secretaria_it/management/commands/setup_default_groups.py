from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

REGULATION_GROUP = 'Regulação'
UBS_GROUP = 'UBS'

class Command(BaseCommand):
    help = 'Cria grupos padrão (Regulação e UBS) se não existirem.'

    def handle(self, *args, **options):
        created = []
        for name in (REGULATION_GROUP, UBS_GROUP):
            _, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created.append(name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Grupos criados: {", ".join(created)}'))
        else:
            self.stdout.write('Grupos já existentes; nada a fazer.')
