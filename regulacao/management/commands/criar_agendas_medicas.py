from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from regulacao.models import AgendaMedica, AgendaMedicaDia, MedicoAmbulatorio


class Command(BaseCommand):
    help = (
        "Cria agendas semanais e por data para todos os médicos ambulatoriais ativos, "
        "com base nas especialidades vinculadas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--inicio",
            dest="inicio",
            default=None,
            help="Data inicial no formato AAAA-MM-DD (padrão: data de hoje).",
        )
        parser.add_argument(
            "--meses",
            dest="meses",
            type=int,
            default=4,
            help="Quantidade de meses (a partir da data inicial) para geração das agendas por dia.",
        )
        parser.add_argument(
            "--dias",
            dest="dias",
            default="0,1,2,3,4",
            help="Dias da semana a considerar (0=segunda ... 6=domingo). Separar por vírgula.",
        )
        parser.add_argument(
            "--capacidade",
            dest="capacidade",
            type=int,
            default=10,
            help="Capacidade padrão por dia/agenda.",
        )
        parser.add_argument(
            "--sobrescrever",
            dest="sobrescrever",
            action="store_true",
            help="Atualiza agendas existentes ajustando capacidade/ativo ao valor informado.",
        )
        parser.add_argument(
            "--somente-semanal",
            dest="somente_semanal",
            action="store_true",
            help="Gera apenas registros de agenda semanal (não gera AgendaMedicaDia).",
        )
        parser.add_argument(
            "--somente-dia",
            dest="somente_dia",
            action="store_true",
            help="Gera apenas registros por dia (não cria/atualiza AgendaMedica).",
        )
        parser.add_argument(
            "--medico",
            dest="medico",
            type=int,
            default=None,
            help="ID de um médico específico para filtrar a geração.",
        )

    def handle(self, *args, **options):
        inicio = self._parse_date(options.get("inicio"))
        meses = max(1, options.get("meses") or 1)
        dias_semana = self._parse_dias(options.get("dias"))
        capacidade = max(0, options.get("capacidade") or 0)
        sobrescrever = bool(options.get("sobrescrever"))
        somente_semanal = bool(options.get("somente_semanal"))
        somente_dia = bool(options.get("somente_dia"))
        medico_id = options.get("medico")

        if somente_semanal and somente_dia:
            raise CommandError("Use apenas uma das flags --somente-semanal ou --somente-dia.")

        medicos_qs = MedicoAmbulatorio.objects.filter(ativo=True)
        if medico_id:
            medicos_qs = medicos_qs.filter(pk=medico_id)
            if not medicos_qs.exists():
                raise CommandError(f"Não há médico ativo com ID {medico_id}.")

        medicos_qs = medicos_qs.prefetch_related("especialidades")

        if not medicos_qs.exists():
            self.stdout.write(self.style.WARNING("Nenhum médico ativo encontrado. Nada a fazer."))
            return

        stats = {
            "weekly_created": 0,
            "weekly_updated": 0,
            "daily_created": 0,
            "daily_updated": 0,
            "medicos_processados": 0,
        }

        with transaction.atomic():
            for medico in medicos_qs:
                especialidades = [e for e in medico.especialidades.all() if getattr(e, "ativa", True)]
                if not especialidades:
                    continue
                stats["medicos_processados"] += 1
                for especialidade in especialidades:
                    if not somente_dia:
                        self._criar_agenda_semanal(
                            medico,
                            especialidade,
                            dias_semana,
                            capacidade,
                            sobrescrever,
                            stats,
                        )
                    if not somente_semanal:
                        self._criar_agenda_por_dia(
                            medico,
                            especialidade,
                            inicio,
                            meses,
                            dias_semana,
                            capacidade,
                            sobrescrever,
                            stats,
                        )

        self.stdout.write(self.style.SUCCESS("Agendas geradas/atualizadas com sucesso."))
        self.stdout.write(
            "Médicos processados: {medicos_processados}\n"
            "Agendas semanais — criadas: {weekly_created}, atualizadas: {weekly_updated}\n"
            "Agendas por dia — criadas: {daily_created}, atualizadas: {daily_updated}".format(**stats)
        )

    def _parse_date(self, value):
        if not value:
            return timezone.localdate()
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError("Formato de data inválido para --inicio (use AAAA-MM-DD).") from exc

    def _parse_dias(self, value):
        raw = (value or "0,1,2,3,4").replace(";", ",")
        dias = []
        for parte in raw.split(","):
            parte = parte.strip()
            if not parte:
                continue
            try:
                dia = int(parte)
            except ValueError as exc:
                raise CommandError(f"Dia da semana inválido: '{parte}'. Use números de 0 a 6.") from exc
            if dia < 0 or dia > 6:
                raise CommandError(f"Dia da semana fora da faixa (0-6): {dia}.")
            dias.append(dia)
        if not dias:
            raise CommandError("Informe ao menos um dia da semana em --dias.")
        return sorted(set(dias))

    def _relativedelta(self, months):
        try:
            from dateutil.relativedelta import relativedelta

            return relativedelta(months=months)
        except Exception:
            class SimpleRelativeDelta:
                def __init__(self, months):
                    self.months = months

                def __radd__(self, other):
                    return other + timedelta(days=30 * self.months)

            return SimpleRelativeDelta(months)

    def _criar_agenda_semanal(self, medico, especialidade, dias, capacidade, sobrescrever, stats):
        for dia in dias:
            obj, created = AgendaMedica.objects.get_or_create(
                medico=medico,
                especialidade=especialidade,
                dia_semana=dia,
                defaults={"capacidade": capacidade, "ativo": True},
            )
            if created:
                stats["weekly_created"] += 1
            elif sobrescrever:
                needs_update = obj.capacidade != capacidade or not obj.ativo
                if needs_update:
                    obj.capacidade = capacidade
                    obj.ativo = True
                    obj.save(update_fields=["capacidade", "ativo", "atualizado_em"])
                    stats["weekly_updated"] += 1

    def _criar_agenda_por_dia(
        self,
        medico,
        especialidade,
        inicio,
        meses,
        dias,
        capacidade,
        sobrescrever,
        stats,
    ):
        delta = self._relativedelta(meses)
        fim = inicio + delta
        dia_atual = inicio
        while dia_atual < fim:
            if dia_atual.weekday() in dias:
                obj, created = AgendaMedicaDia.objects.get_or_create(
                    medico=medico,
                    especialidade=especialidade,
                    data=dia_atual,
                    defaults={"capacidade": capacidade, "ativo": True},
                )
                if created:
                    stats["daily_created"] += 1
                elif sobrescrever:
                    needs_update = obj.capacidade != capacidade or not obj.ativo
                    if needs_update:
                        obj.capacidade = capacidade
                        obj.ativo = True
                        obj.save(update_fields=["capacidade", "ativo", "atualizado_em"])
                        stats["daily_updated"] += 1
            dia_atual += timedelta(days=1)
