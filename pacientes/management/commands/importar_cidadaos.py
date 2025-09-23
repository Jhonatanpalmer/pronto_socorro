from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils.dateparse import parse_date, parse_datetime

from pacientes.models import Paciente, validate_cpf
from django.core.exceptions import ValidationError


ALT_NAMES = {
    "nome": [
        "nome",
        "nm_cidadao",
        "nm_pessoa",
        "nm_cidadao_ou_responsavel",
        "no_cidadao",
        "no_cidadao_filtro",
    ],
    "cpf": ["cpf", "nu_cpf", "cpf_cidadao", "nr_cpf"],
    "cns": ["cns", "nu_cns", "cns_cidadao", "nr_cns", "cartao_sus"],
    "data_nascimento": [
        "data_nascimento",
        "dt_nascimento",
        "nascimento",
        "data_nasc",
        "dt_nasc",
    ],
    "telefone": [
        "telefone",
        "nu_telefone",
        "fone",
        "telefone1",
        "telefone_contato",
        "nr_telefone",
        # e-SUS comuns
        "nu_telefone_residencial",
        "nu_telefone_celular",
        "nu_telefone_contato",
    ],
    # Endereço (tentativa de composição)
    "logradouro": ["logradouro", "ds_logradouro", "endereco", "rua"],
    "numero": ["numero", "nr_numero", "num_residencia", "nr_resid"],
    "bairro": ["bairro", "ds_bairro"],
    "municipio": ["municipio", "nm_municipio", "cidade"],
    "uf": ["uf", "sg_uf", "estado"],
}


def pick_first(row: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def normalize_digits(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = "".join(ch for ch in str(value) if ch.isdigit())
    return s or None


def normalize_cpf(value: Optional[str]) -> Optional[str]:
    cpf = normalize_digits(value)
    if not cpf:
        return None
    try:
        validate_cpf(cpf)
        return cpf
    except ValidationError:
        return None


def normalize_cns(value: Optional[str]) -> Optional[str]:
    return normalize_digits(value)


def normalize_telefone(value: Optional[str]) -> Optional[str]:
    tel = normalize_digits(value)
    if not tel:
        return None
    # Mantém até 20 caracteres (campo do modelo)
    return tel[:20]


def to_date(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if hasattr(value, "date"):
        try:
            return value.date().isoformat()
        except Exception:
            pass
    # tenta ISO/datetime string
    try:
        dt = parse_datetime(str(value))
        if dt:
            return dt.date().isoformat()
    except Exception:
        pass
    d = parse_date(str(value))
    return d.isoformat() if d else None


def build_endereco(row: Dict[str, Any]) -> str:
    logradouro = pick_first(row, ALT_NAMES["logradouro"]) or ""
    numero = pick_first(row, ALT_NAMES["numero"]) or ""
    bairro = pick_first(row, ALT_NAMES["bairro"]) or ""
    municipio = pick_first(row, ALT_NAMES["municipio"]) or ""
    uf = pick_first(row, ALT_NAMES["uf"]) or ""
    partes = [str(p).strip() for p in [logradouro, numero, bairro, municipio, uf] if str(p).strip()]
    endereco = ", ".join(partes)
    # Campo do modelo tem max_length=30 (apesar de ser TextField), então truncamos
    return endereco[:30]


class Command(BaseCommand):
    help = (
        "Importa cidadãos do e-SUS (tb_cidadao) para o modelo Paciente. "
        "Faz upsert usando prioridade de matching: CPF > CNS > (nome + data_nascimento)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limita a quantidade total de linhas a processar (0 = todos)")
        parser.add_argument("--offset", type=int, default=0, help="Deslocamento inicial (offset)")
        parser.add_argument("--chunk-size", type=int, default=1000, help="Tamanho do lote por consulta ao PostgreSQL")
        parser.add_argument("--schema", type=str, default="", help="Schema do PostgreSQL (ex.: public). Se vazio, usa o search_path padrão")
        parser.add_argument("--dry-run", action="store_true", help="Não grava no banco local, apenas simula e mostra contagem")
        parser.add_argument("--verbose-log", action="store_true", help="Exibe logs por registro (pode ser bem verboso)")

    def handle(self, *args, **opts):
        limit = int(opts["limit"]) if opts["limit"] else 0
        offset = int(opts["offset"]) if opts["offset"] else 0
        chunk_size = max(1, int(opts["chunk_size"]))
        schema = opts["schema"].strip()
        dry_run = bool(opts["dry_run"])
        verbose_log = bool(opts["verbose_log"])

        table = "tb_cidadao"
        qualified_table = f"{schema}.{table}" if schema else table

        total_read = 0
        created = 0
        updated = 0
        skipped = 0

        with connections["esus"].cursor() as cursor:
            # Verifica colunas disponíveis
            cursor.execute(f"SELECT * FROM {qualified_table} LIMIT 0")
            colnames = [c[0] for c in cursor.description]
            self.stdout.write(f"Colunas detectadas em {qualified_table}: {', '.join(colnames)}")

            while True:
                if limit and total_read >= limit:
                    break
                fetch = chunk_size
                if limit:
                    remaining = limit - total_read
                    fetch = min(fetch, remaining)

                sql = f"SELECT * FROM {qualified_table} LIMIT %s OFFSET %s"
                cursor.execute(sql, [fetch, offset])
                rows = cursor.fetchall()
                if not rows:
                    break

                batch = [dict(zip(colnames, r)) for r in rows]
                total_read += len(batch)
                offset += len(batch)

                if dry_run:
                    # Apenas simula processamento
                    for row in batch:
                        nome = pick_first(row, ALT_NAMES["nome"]) or ""
                        cpf = normalize_cpf(pick_first(row, ALT_NAMES["cpf"]))
                        cns = normalize_cns(pick_first(row, ALT_NAMES["cns"]))
                        data_nasc = to_date(pick_first(row, ALT_NAMES["data_nascimento"]))
                        if not any([cpf, cns]) and not (nome and data_nasc):
                            skipped += 1
                        else:
                            # não sabemos ainda se cria ou atualiza sem consultar local, então apenas conta como processável
                            pass
                    continue

                # Grava em transação por lote
                with transaction.atomic():
                    for row in batch:
                        nome = pick_first(row, ALT_NAMES["nome"]) or ""
                        cpf = normalize_cpf(pick_first(row, ALT_NAMES["cpf"]))
                        cns = normalize_cns(pick_first(row, ALT_NAMES["cns"]))
                        data_nasc = to_date(pick_first(row, ALT_NAMES["data_nascimento"]))
                        telefone = normalize_telefone(pick_first(row, ALT_NAMES["telefone"])) or ""
                        endereco = build_endereco(row)

                        if not nome:
                            # Sem nome não conseguimos popular o modelo (obrigatório)
                            skipped += 1
                            if verbose_log:
                                self.stderr.write("Registro ignorado: nome ausente")
                            continue
                        if not data_nasc:
                            skipped += 1
                            if verbose_log:
                                self.stderr.write(f"Registro '{nome}' ignorado: data de nascimento ausente/inválida")
                            continue

                        paciente: Optional[Paciente] = None
                        # Prioridade de matching: CPF -> CNS -> (nome + data_nascimento)
                        if cpf:
                            paciente = Paciente.objects.filter(cpf=cpf).first()
                        if not paciente and cns:
                            paciente = Paciente.objects.filter(cns=cns).first()
                        if not paciente:
                            paciente = Paciente.objects.filter(nome=nome, data_nascimento=data_nasc).first()

                        defaults = {
                            "nome": nome,
                            "cns": cns,
                            "data_nascimento": data_nasc,
                            "endereco": endereco,
                            "telefone": telefone,
                        }
                        # cpf só define quando válido
                        if cpf:
                            defaults["cpf"] = cpf

                        if paciente:
                            # Atualiza somente campos diferentes
                            changed = False
                            for k, v in defaults.items():
                                if getattr(paciente, k) != v:
                                    setattr(paciente, k, v)
                                    changed = True
                            if changed:
                                paciente.save()
                                updated += 1
                                if verbose_log:
                                    self.stdout.write(f"Atualizado: {paciente.nome} ({paciente.id})")
                            else:
                                # Sem mudança
                                if verbose_log:
                                    self.stdout.write(f"Sem mudanças: {paciente.nome} ({paciente.id})")
                        else:
                            # Cria novo
                            try:
                                paciente = Paciente.objects.create(
                                    nome=nome,
                                    cpf=cpf,
                                    cns=cns,
                                    data_nascimento=data_nasc,
                                    endereco=endereco,
                                    telefone=telefone,
                                )
                                created += 1
                                if verbose_log:
                                    self.stdout.write(f"Criado: {paciente.nome} ({paciente.id})")
                            except ValidationError as ve:
                                skipped += 1
                                self.stderr.write(f"Registro ignorado por validação: {ve}")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN concluído. Lidos: {total_read}, processáveis: ~{total_read - skipped}, ignorados (por falta de chaves): {skipped}."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Importação concluída. Lidos: {total_read}, Criados: {created}, Atualizados: {updated}, Ignorados: {skipped}."
            ))
