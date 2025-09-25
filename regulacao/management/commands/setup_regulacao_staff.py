from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, User
from secretaria_it.models import GroupAccess
from typing import List, Tuple
import secrets

GROUP_NAME = 'Regulação'


def ensure_group() -> Group:
    group, _ = Group.objects.get_or_create(name=GROUP_NAME)
    access, _ = GroupAccess.objects.get_or_create(group=group)
    if not access.can_regulacao:
        access.can_regulacao = True
        access.save()
    return group


def parse_user_spec(spec: str) -> Tuple[str, str, str]:
    """
    Parse a user spec in the form username[:password[:email]]
    Returns (username, password, email)
    """
    parts = (spec or '').split(':')
    username = (parts[0] or '').strip()
    if not username:
        raise CommandError('Username cannot be empty in --user spec.')
    password = (parts[1].strip() if len(parts) > 1 and parts[1] else secrets.token_urlsafe(12))
    email = (parts[2].strip() if len(parts) > 2 else '')
    return username, password, email


class Command(BaseCommand):
    help = (
        'Create or update the "Regulação" group with access rights and optionally create users for this staff.\n'
        'Usage examples:\n'
        '  python manage.py setup_regulacao_staff\n'
        '  python manage.py setup_regulacao_staff --user joana\n'
        '  python manage.py setup_regulacao_staff --user joao:Senha@123:joao@example.com --user maria::maria@example.com\n'
        'Notes:\n'
        '  - If password is omitted, a secure random password will be generated and printed.\n'
        '  - Users created will NOT be linked to any UBS profile and will see all requests.\n'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user', action='append', dest='users', default=[],
            help='User spec to create/add to the Regulação group: username[:password[:email]]. Can be provided multiple times.'
        )
        parser.add_argument(
            '--staff', action='store_true', default=False,
            help='Mark created users as is_staff (allows Django admin access). Default is False.'
        )
        parser.add_argument(
            '--no-output-password', action='store_true', default=False,
            help='Do not print generated passwords to stdout.'
        )

    def handle(self, *args, **options):
        group = ensure_group()
        self.stdout.write(self.style.SUCCESS(f'Group "{GROUP_NAME}" is ready with Regulação access.'))

        users_specs: List[str] = options.get('users') or []
        make_staff: bool = bool(options.get('staff'))
        quiet_pw: bool = bool(options.get('no_output_password'))

        for spec in users_specs:
            username, password, email = parse_user_spec(spec)
            user, created = User.objects.get_or_create(username=username, defaults={'email': email or ''})
            if created:
                user.set_password(password)
                user.is_staff = make_staff
                user.save()
                action = 'created'
            else:
                action = 'updated'
                changed = False
                if email and user.email != email:
                    user.email = email
                    changed = True
                if make_staff and not user.is_staff:
                    user.is_staff = True
                    changed = True
                if changed:
                    user.save()
            user.groups.add(group)
            msg = f'User {username} {action} and added to group "{GROUP_NAME}".'
            if created and not quiet_pw:
                msg += f' Password: {password}'
            self.stdout.write(self.style.SUCCESS(msg))

        if not users_specs:
            self.stdout.write('No users specified. You can add users later and only add them to the "Regulação" group.')
            self.stdout.write('To create a user now, run again with: --user username[:password[:email]]')
