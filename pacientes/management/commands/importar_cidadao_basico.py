from datetime import date, datetime
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime

from pacientes.models import Paciente
from pacientes.services import get_esus_connection


def _to_date(value) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed_dt = parse_datetime(str(value))
    if parsed_dt:
        return parsed_dt.date()
    parsed_date = parse_date(str(value))
    return parsed_date


class Command(BaseCommand):
    help = "Importa dados básicos (nome, data de nascimento, filiação) de tl_cidadao para o cadastro de Pacientes."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="", help="Schema do PostgreSQL (ex.: public). Se vazio, usa o padrão.")
        parser.add_argument("--limit", type=int, default=0, help="Número máximo de linhas a processar (0 = todas).")
        parser.add_argument("--offset", type=int, default=0, help="Deslocamento inicial para leitura.")
        parser.add_argument("--chunk-size", type=int, default=1000, help="Quantidade de registros por lote na consulta.")

    def handle(self, *args, **opts):
        schema = opts["schema"].strip()
        limit = int(opts["limit"]) if opts["limit"] else 0
        offset = int(opts["offset"]) if opts["offset"] else 0
        chunk_size = max(1, int(opts["chunk_size"]))

        table = "tl_cidadao"
        qualified = f"{schema}.{table}" if schema else table

        total = created = updated = skipped = 0

        conn = get_esus_connection()
        with conn.cursor() as cursor:
            while not limit or total < limit:
                fetch = min(chunk_size, max(limit - total, 0)) if limit else chunk_size
                if limit and fetch <= 0:
                    break

                sql = f"SELECT no_cidadao, dt_nascimento, no_mae, no_pai FROM {qualified} LIMIT %s OFFSET %s"
                cursor.execute(sql, [fetch, offset])
                rows = cursor.fetchall()
                if not rows:
                    break

                offset += len(rows)
                total += len(rows)

                with transaction.atomic():
                    for nome, dt_nasc, nome_mae, nome_pai in rows:
                        nome = (nome or "").strip()
                        if not nome:
                            skipped += 1
                            continue

                        data_convertida = _to_date(dt_nasc)
                        mae = (nome_mae or "").strip()
                        pai = (nome_pai or "").strip()

                        qs = Paciente.objects.filter(nome=nome)
                        if data_convertida:
                            qs = qs.filter(data_nascimento=data_convertida)
                        if not qs and mae:
                            qs = Paciente.objects.filter(nome=nome, nome_mae=mae)

                        if paciente := qs.first():
                            changed_fields = []
                            if data_convertida and paciente.data_nascimento != data_convertida:
                                paciente.data_nascimento = data_convertida
                                changed_fields.append("data_nascimento")
                            if mae and not paciente.nome_mae:
                                paciente.nome_mae = mae
                                changed_fields.append("nome_mae")
                            if pai and not paciente.nome_pai:
                                paciente.nome_pai = pai
                                changed_fields.append("nome_pai")
                            if changed_fields:
                                paciente.save(update_fields=changed_fields)
                                updated += 1
                            else:
                                skipped += 1
                        else:
                            paciente = Paciente(
                                nome=nome,
                                data_nascimento=data_convertida,
                                nome_mae=mae,
                                nome_pai=pai,
                            )
                            paciente.save()
                            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Processamento concluído. Lidos: {total}, Criados: {created}, Atualizados: {updated}, Ignorados: {skipped}."
        ))
