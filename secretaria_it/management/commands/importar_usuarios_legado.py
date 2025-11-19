import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from regulacao.models import UBS, UsuarioUBS
from secretaria_it.models import GroupAccess


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, (datetime,)):
        dt = value
    else:
        text = str(value)
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


class Command(BaseCommand):
    help = "Importa usuários, grupos e vínculos da base SQLite legado (db.sqlite3 por padrão)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sqlite-path",
            default="db.sqlite3",
            help="Caminho para o arquivo SQLite legado contendo as tabelas auth_*.",
        )

    def handle(self, *args, **options):
        path = Path(options["sqlite_path"])
        if not path.exists():
            raise CommandError(f"Arquivo SQLite não encontrado: {path}")

        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        try:
            with transaction.atomic():
                ubs_map = self._import_ubs(conn)
                group_map = self._import_groups(conn)
                self._import_group_access(conn, group_map)
                user_map, created_users, updated_users = self._import_users(conn)
                assigned_groups = self._assign_user_groups(conn, user_map, group_map)
                vinculos = self._assign_usuario_ubs(conn, user_map, ubs_map)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS(
            f"Usuários criados: {created_users}, atualizados: {updated_users}."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Vínculos com grupos aplicados para {assigned_groups} usuários."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Vínculos UBS sincronizados: {vinculos}."
        ))

    def _import_ubs(self, conn):
        rows = conn.execute(
            "SELECT id, nome, endereco, telefone, email, responsavel, ativa FROM regulacao_ubs"
        ).fetchall()
        mapping = {}
        for row in rows:
            ubs, _ = UBS.objects.update_or_create(
                nome=row["nome"],
                defaults={
                    "endereco": row["endereco"] or "",
                    "telefone": row["telefone"] or "",
                    "email": row["email"] or "",
                    "responsavel": row["responsavel"] or "",
                    "ativa": bool(row["ativa"]),
                },
            )
            mapping[row["id"]] = ubs
        return mapping

    def _import_groups(self, conn):
        rows = conn.execute("SELECT id, name FROM auth_group").fetchall()
        mapping = {}
        for row in rows:
            group, _ = Group.objects.update_or_create(name=row["name"])
            mapping[row["id"]] = group
        return mapping

    def _import_group_access(self, conn, group_map):
        rows = conn.execute(
            "SELECT group_id, can_pacientes, can_viagens, can_tfd, can_regulacao, "
            "can_users_admin, can_motorista, can_rh, can_veiculos FROM secretaria_it_groupaccess"
        ).fetchall()
        for row in rows:
            group = group_map.get(row["group_id"])
            if not group:
                continue
            access, _ = GroupAccess.objects.get_or_create(group=group)
            access.can_pacientes = bool(row["can_pacientes"])
            access.can_viagens = bool(row["can_viagens"])
            access.can_tfd = bool(row["can_tfd"])
            access.can_regulacao = bool(row["can_regulacao"])
            access.can_users_admin = bool(row["can_users_admin"])
            access.can_motorista = bool(row["can_motorista"])
            access.can_rh = bool(row["can_rh"])
            access.can_veiculos = bool(row["can_veiculos"])
            access.save()

    def _import_users(self, conn):
        User = get_user_model()
        rows = conn.execute(
            "SELECT id, username, password, first_name, last_name, email, is_staff, "
            "is_active, is_superuser, last_login, date_joined FROM auth_user"
        ).fetchall()
        mapping = {}
        created = updated = 0
        for row in rows:
            defaults = {
                "password": row["password"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "is_staff": bool(row["is_staff"]),
                "is_active": bool(row["is_active"]),
                "is_superuser": bool(row["is_superuser"]),
                "last_login": _parse_datetime(row["last_login"]),
                "date_joined": _parse_datetime(row["date_joined"]),
            }
            user, created_flag = User.objects.update_or_create(
                username=row["username"], defaults=defaults
            )
            mapping[row["id"]] = user
            if created_flag:
                created += 1
            else:
                updated += 1
        return mapping, created, updated

    def _assign_user_groups(self, conn, user_map, group_map):
        rows = conn.execute("SELECT user_id, group_id FROM auth_user_groups").fetchall()
        per_user = defaultdict(list)
        for row in rows:
            if group := group_map.get(row["group_id"]):
                per_user[row["user_id"]].append(group)
        applied = 0
        for legacy_id, user in user_map.items():
            groups = per_user.get(legacy_id, [])
            user.groups.set(groups)
            if groups:
                applied += 1
        return applied

    def _assign_usuario_ubs(self, conn, user_map, ubs_map):
        rows = conn.execute("SELECT user_id, ubs_id FROM regulacao_usuarioubs").fetchall()
        applied = 0
        for row in rows:
            user = user_map.get(row["user_id"])
            ubs = ubs_map.get(row["ubs_id"])
            if not user or not ubs:
                continue
            UsuarioUBS.objects.update_or_create(user=user, defaults={"ubs": ubs})
            applied += 1
        return applied
