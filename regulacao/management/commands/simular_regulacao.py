import random
import string
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pacientes.models import Paciente
from regulacao.models import (
    Especialidade,
    LocalAtendimento,
    MedicoAmbulatorio,
    MedicoSolicitante,
    RegulacaoConsulta,
    RegulacaoExame,
    TipoExame,
    UBS,
)


class Command(BaseCommand):
    help = "Gera dados simulados de regulações de exames e consultas para testes."

    STATUS_DISTRIBUTION = [
        ("fila", 0.35),
        ("autorizado", 0.30),
        ("pendente", 0.20),
        ("negado", 0.15),
    ]

    PRIORIDADES = ["normal", "media", "alta"]
    RESULTADOS = ["pendente", "compareceu", "faltou"]

    JUSTIFICATIVAS = [
        "Paciente com sintomas persistentes há mais de 30 dias.",
        "Solicitação de acompanhamento para condição crônica.",
        "Avaliação complementar solicitada pelo médico assistente.",
        "Exame preventivo conforme protocolo municipal.",
        "Paciente apresentou agravamento recente do quadro clínico.",
    ]

    MOTIVOS_NEGACAO = [
        "Documentação incompleta no momento da análise.",
        "Não se enquadra nos critérios do protocolo clínico.",
        "Paciente já possui agendamento ativo para o mesmo procedimento.",
        "Solicitação duplicada identificada pela regulação.",
    ]

    PENDENCIAS = [
        "Aguardar envio de laudos complementares pela UBS.",
        "Falta informação clínica detalhada do médico solicitante.",
        "Necessário anexar exames anteriores para comparação.",
    ]

    OBS_REGULACAO = [
        "Encaminhado para realização no prestador conveniado.",
        "Paciente será contatado pela central de regulação.",
        "Agendamento realizado conforme disponibilidade informada.",
    ]

    LOCAL_NOMES = [
        "Hospital Municipal Iturama",
        "Clínica Integrada São Lucas",
        "Centro de Imagens Vida",
        "Laboratório Municipal",
        "Ambulatório Regional",
    ]

    ESPECIALIDADES = [
        "Cardiologia",
        "Ortopedia",
        "Dermatologia",
        "Endocrinologia",
        "Neurologia",
        "Pediatria",
        "Ginecologia",
        "Oftalmologia",
        "Otorrino",
        "Reumatologia",
    ]

    TIPOS_EXAME = [
        "Ultrassonografia Abdominal",
        "Tomografia de Tórax",
        "Ressonância Magnética",
        "Hemograma Completo",
        "Raio-X de Tórax",
        "Eletrocardiograma",
        "Teste de Esforço",
        "Mamografia",
        "Densitometria Óssea",
        "Colonoscopia",
    ]

    UBS_NOMES = [
        "UBS Central",
        "UBS São Sebastião",
        "UBS Jardim Primavera",
        "UBS Nossa Senhora Aparecida",
        "UBS Bela Vista",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--exames",
            type=int,
            default=1000,
            help="Quantidade total desejada de regulações de exames (padrão: 1000).",
        )
        parser.add_argument(
            "--consultas",
            type=int,
            default=1000,
            help="Quantidade total desejada de regulações de consultas (padrão: 1000).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Seed opcional para o gerador de números aleatórios (reprodutível).",
        )
        parser.add_argument(
            "--limpar",
            action="store_true",
            help="Remove todos os registros existentes de regulações antes de criar os simulados.",
        )

    def handle(self, *args, **options):
        exames_target = max(0, options["exames"])
        consultas_target = max(0, options["consultas"])
        seed = options.get("seed")
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()

        if options.get("limpar"):
            self._limpar_dados()

        base = self._garantir_dados_base()

        with transaction.atomic():
            exames = self._gerar_exames(exames_target, base)
            consultas = self._gerar_consultas(consultas_target, base)

        self.stdout.write(self.style.SUCCESS("Simulação concluída."))
        self.stdout.write(
            f"Regulações de exames: total={RegulacaoExame.objects.count()} (criados {exames['criados']})"
        )
        self.stdout.write(
            f" - Distribuição: fila={exames['status'].get('fila', 0)}, pendente={exames['status'].get('pendente', 0)}, autorizado={exames['status'].get('autorizado', 0)}, negado={exames['status'].get('negado', 0)}"
        )
        self.stdout.write(
            f"Regulações de consultas: total={RegulacaoConsulta.objects.count()} (criados {consultas['criados']})"
        )
        self.stdout.write(
            f" - Distribuição: fila={consultas['status'].get('fila', 0)}, pendente={consultas['status'].get('pendente', 0)}, autorizado={consultas['status'].get('autorizado', 0)}, negado={consultas['status'].get('negado', 0)}"
        )

    # ---------- Helpers ----------

    def _limpar_dados(self):
        self.stdout.write("Removendo regulações anteriores...")
        RegulacaoExame.objects.all().delete()
        RegulacaoConsulta.objects.all().delete()

    def _garantir_dados_base(self):
        ubs_list = self._criar_ubs()
        tipos_exame = self._criar_tipos_exame()
        especialidades = self._criar_especialidades()
        locais = self._criar_locais()
        medicos_solicitantes = self._criar_medicos_solicitantes(ubs_list)
        medicos_ambulatorio = self._criar_medicos_ambulatorio(especialidades)
        pacientes = self._garantir_pacientes()
        reguladores = list(get_user_model().objects.filter(is_staff=True))

        medicos_por_especialidade = {}
        for esp in especialidades:
            medicos = list(esp.medicos_ambulatorio.filter(ativo=True))
            if medicos:
                medicos_por_especialidade[esp.id] = medicos

        return {
            "ubs": ubs_list,
            "tipos_exame": tipos_exame,
            "especialidades": especialidades,
            "locais": locais,
            "medicos_solicitantes": medicos_solicitantes,
            "medicos_ambulatorio": medicos_ambulatorio,
            "medicos_por_especialidade": medicos_por_especialidade,
            "pacientes": pacientes,
            "reguladores": reguladores,
        }

    def _criar_ubs(self):
        ubs_list = []
        for nome in self.UBS_NOMES:
            ubs, _ = UBS.objects.get_or_create(
                nome=nome,
                defaults={
                    "endereco": f"{nome} - Endereço {random.randint(10, 999)}",
                    "telefone": f"(34) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                    "email": f"contato_{self._slugify(nome)}@saude.gov.br",
                },
            )
            ubs_list.append(ubs)
        if not ubs_list:
            ubs_list.append(
                UBS.objects.create(
                    nome="UBS Simulada",
                    endereco="Rua Principal, 100",
                    telefone="(34) 99999-0000",
                )
            )
        return ubs_list

    def _criar_tipos_exame(self):
        tipos = []
        for idx, nome in enumerate(self.TIPOS_EXAME, start=1):
            tipos_exame, _ = TipoExame.objects.get_or_create(
                nome=nome,
                defaults={
                    "codigo": f"EXA-{idx:03d}",
                    "descricao": f"Exame simulado: {nome}.",
                    "codigo_sus": f"{idx:05d}",
                    "valor": random.randint(50, 500),
                    "ativo": True,
                },
            )
            tipos.append(tipos_exame)
        return tipos

    def _criar_especialidades(self):
        especialidades = []
        for nome in self.ESPECIALIDADES:
            esp, _ = Especialidade.objects.get_or_create(
                nome=nome,
                defaults={"descricao": f"Especialidade simulada de {nome}.", "ativa": True},
            )
            especialidades.append(esp)
        return especialidades

    def _criar_locais(self):
        locais = []
        for nome in self.LOCAL_NOMES:
            loc, _ = LocalAtendimento.objects.get_or_create(
                nome=nome,
                defaults={
                    "tipo": random.choice([choice[0] for choice in LocalAtendimento.TIPO_CHOICES]),
                    "endereco": f"{nome} - Av. Principal, {random.randint(1, 500)}",
                    "telefone": f"(34) 3{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                },
            )
            locais.append(loc)
        return locais

    def _criar_medicos_solicitantes(self, ubs_list):
        medicos = []
        base_nomes = [
            "Carlos", "Mariana", "Fernanda", "João", "Patrícia", "Ricardo", "Luciana",
            "Roberta", "Guilherme", "Sueli", "André", "Viviane", "Rafael", "Sandra",
            "Henrique", "Juliana", "Marcelo", "Natália",
        ]
        for idx, nome in enumerate(base_nomes, start=1):
            crm = f"CRM{idx:05d}"
            medico, created = MedicoSolicitante.objects.get_or_create(
                crm=crm,
                defaults={
                    "nome": f"Dr(a). {nome} Simulado",
                    "especialidade": random.choice(self.ESPECIALIDADES),
                    "telefone": f"(34) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                    "email": f"dr{idx}@saude.iturama.gov.br",
                    "ubs_padrao": random.choice(ubs_list),
                    "ativo": True,
                },
            )
            if created:
                medicos.append(medico)
            else:
                medicos.append(medico)
        return medicos

    def _criar_medicos_ambulatorio(self, especialidades):
        medicos = []
        base_nomes = [
            "Alberto", "Beatriz", "Cláudio", "Daniela", "Eduardo", "Fabiana", "Gabriel",
            "Helena", "Isabela", "Jorge", "Karen", "Leandro", "Monique", "Nelson",
        ]
        for idx, nome in enumerate(base_nomes, start=1):
            crm = f"AMB{idx:05d}"
            medico, _ = MedicoAmbulatorio.objects.get_or_create(
                crm=crm,
                defaults={
                    "nome": f"Dr(a). {nome} Ambulatório",
                    "telefone": f"(34) 34{random.randint(100,999)}-{random.randint(1000,9999)}",
                    "email": f"amb{idx}@saude.iturama.gov.br",
                    "ativo": True,
                },
            )
            if medico.especialidades.count() == 0 and especialidades:
                qty = random.randint(1, min(3, len(especialidades)))
                medico.especialidades.set(random.sample(especialidades, qty))
            medicos.append(medico)
        return medicos

    def _garantir_pacientes(self):
        pacientes = list(Paciente.objects.all())
        if len(pacientes) >= 200:
            return pacientes

        faltam = 200 - len(pacientes)
        for idx in range(faltam):
            numero = len(pacientes) + idx + 1
            paciente = Paciente.objects.create(
                nome=f"Paciente Simulado {numero}",
                cpf=None,
                data_nascimento=date(1990, 1, 1) + timedelta(days=random.randint(0, 12000)),
                logradouro=f"Rua {random.randint(1, 200)}",
                numero=str(random.randint(10, 999)),
                bairro="Centro",
                telefone=f"(34) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            )
            pacientes.append(paciente)
        return pacientes

    def _gerar_exames(self, target, base):
        criados = 0
        status_counter = {key: 0 for key, _ in self.STATUS_DISTRIBUTION}

        existentes = RegulacaoExame.objects.count()
        to_create = max(target - existentes, 0)
        if to_create == 0:
            return {"criados": 0, "status": status_counter}

        prioridades = self.PRIORIDADES
        locais = base["locais"]
        pacientes = base["pacientes"]
        ubs_list = base["ubs"]
        tipos_exame = base["tipos_exame"]
        medicos_solicitantes = base["medicos_solicitantes"]
        reguladores = base["reguladores"]

        for _ in range(to_create):
            status = random.choices(
                [choice[0] for choice in self.STATUS_DISTRIBUTION],
                weights=[choice[1] for choice in self.STATUS_DISTRIBUTION],
                k=1,
            )[0]
            status_counter[status] += 1

            paciente = random.choice(pacientes)
            ubs = random.choice(ubs_list)
            medico_sol = random.choice(medicos_solicitantes)
            tipo_exame = random.choice(tipos_exame)

            prioridade = random.choices(prioridades, weights=[0.6, 0.3, 0.1])[0]
            justificativa = random.choice(self.JUSTIFICATIVAS)
            observ_solic = random.choice(self.OBS_REGULACAO)

            regulador = random.choice(reguladores) if reguladores else None

            exame = RegulacaoExame(
                paciente=paciente,
                ubs_solicitante=ubs,
                medico_solicitante=medico_sol,
                tipo_exame=tipo_exame,
                justificativa=justificativa,
                prioridade=prioridade,
                observacoes_solicitacao=observ_solic,
                status=status,
                regulador=regulador,
                numero_pedido=self._gerar_numero_pedido("EXA", ubs.id),
            )

            if status in {"autorizado", "pendente", "negado"}:
                exame.motivo_decisao = (
                    "Exame autorizado conforme protocolo." if status == "autorizado" else random.choice(self.MOTIVOS_NEGACAO)
                )

            if status == "autorizado":
                local = random.choice(locais)
                dias_a_frente = random.randint(3, 45)
                data_agendada = timezone.localdate() + timedelta(days=dias_a_frente)
                hora = time(hour=random.randint(7, 16), minute=random.choice([0, 15, 30, 45]))
                exame.local_realizacao = local.nome
                exame.data_agendada = data_agendada
                exame.hora_agendada = hora
                exame.medico_atendente = random.choice(medicos_solicitantes)
                exame.observacoes_regulacao = random.choice(self.OBS_REGULACAO)

            if status == "pendente":
                exame.pendencia_motivo = random.choice(self.PENDENCIAS)

            exame.save()

            data_solicitacao = timezone.now() - timedelta(days=random.randint(0, 160))
            update_kwargs = {
                "data_solicitacao": data_solicitacao,
                "criado_em": data_solicitacao,
            }
            if status in {"autorizado", "pendente", "negado"}:
                data_regulacao = data_solicitacao + timedelta(days=random.randint(1, 7))
                update_kwargs["data_regulacao"] = data_regulacao
                update_kwargs["atualizado_em"] = data_regulacao
                if status == "pendente":
                    update_kwargs["pendencia_aberta_em"] = data_regulacao
                    if exame.regulador:
                        update_kwargs["pendencia_aberta_por_id"] = exame.regulador_id
            else:
                update_kwargs["atualizado_em"] = data_solicitacao

            RegulacaoExame.objects.filter(pk=exame.pk).update(**update_kwargs)

            if status == "autorizado" and exame.data_agendada:
                if exame.data_agendada < timezone.localdate():
                    resultado = random.choices(self.RESULTADOS, weights=[0.5, 0.4, 0.1])[0]
                    RegulacaoExame.objects.filter(pk=exame.pk).update(
                        resultado_atendimento=resultado,
                        resultado_em=timezone.now() - timedelta(days=random.randint(0, 30)),
                    )

            criados += 1

        return {"criados": criados, "status": status_counter}

    def _gerar_consultas(self, target, base):
        criados = 0
        status_counter = {key: 0 for key, _ in self.STATUS_DISTRIBUTION}

        existentes = RegulacaoConsulta.objects.count()
        to_create = max(target - existentes, 0)
        if to_create == 0:
            return {"criados": 0, "status": status_counter}

        pacientes = base["pacientes"]
        ubs_list = base["ubs"]
        especialidades = base["especialidades"]
        medicos_solicitantes = base["medicos_solicitantes"]
        reguladores = base["reguladores"]
        locais = base["locais"]
        medicos_por_especialidade = base["medicos_por_especialidade"]
        medicos_ambulatorio = base["medicos_ambulatorio"]

        for _ in range(to_create):
            status = random.choices(
                [choice[0] for choice in self.STATUS_DISTRIBUTION],
                weights=[choice[1] for choice in self.STATUS_DISTRIBUTION],
                k=1,
            )[0]
            status_counter[status] += 1

            paciente = random.choice(pacientes)
            ubs = random.choice(ubs_list)
            medico_sol = random.choice(medicos_solicitantes)
            especialidade = random.choice(especialidades)
            prioridade = random.choices(self.PRIORIDADES, weights=[0.65, 0.25, 0.1])[0]
            justificativa = random.choice(self.JUSTIFICATIVAS)
            observ_solic = random.choice(self.OBS_REGULACAO)
            regulador = random.choice(reguladores) if reguladores else None

            consulta = RegulacaoConsulta(
                paciente=paciente,
                ubs_solicitante=ubs,
                medico_solicitante=medico_sol,
                especialidade=especialidade,
                justificativa=justificativa,
                prioridade=prioridade,
                observacoes_solicitacao=observ_solic,
                status=status,
                regulador=regulador,
            )

            if status in {"autorizado", "pendente", "negado"}:
                consulta.motivo_decisao = (
                    "Consulta autorizada para atendimento especializado." if status == "autorizado" else random.choice(self.MOTIVOS_NEGACAO)
                )

            if status == "autorizado":
                dias_a_frente = random.randint(5, 60)
                data_agendada = timezone.localdate() + timedelta(days=dias_a_frente)
                hora = time(hour=random.randint(7, 16), minute=random.choice([0, 20, 40]))
                consulta.data_agendada = data_agendada
                consulta.hora_agendada = hora
                consulta.local_atendimento = random.choice(locais).nome
                medicos_disponiveis = medicos_por_especialidade.get(especialidade.id)
                if medicos_disponiveis:
                    consulta.medico_atendente = random.choice(medicos_disponiveis)
                elif medicos_ambulatorio:
                    consulta.medico_atendente = random.choice(medicos_ambulatorio)
                consulta.observacoes_regulacao = random.choice(self.OBS_REGULACAO)

            if status == "pendente":
                consulta.pendencia_motivo = random.choice(self.PENDENCIAS)

            consulta.save()

            data_solicitacao = timezone.now() - timedelta(days=random.randint(0, 180))
            update_kwargs = {
                "data_solicitacao": data_solicitacao,
                "criado_em": data_solicitacao,
            }
            if status in {"autorizado", "pendente", "negado"}:
                data_regulacao = data_solicitacao + timedelta(days=random.randint(1, 10))
                update_kwargs["data_regulacao"] = data_regulacao
                update_kwargs["atualizado_em"] = data_regulacao
                if status == "pendente":
                    update_kwargs["pendencia_aberta_em"] = data_regulacao
                    if consulta.regulador:
                        update_kwargs["pendencia_aberta_por_id"] = consulta.regulador_id
            else:
                update_kwargs["atualizado_em"] = data_solicitacao

            RegulacaoConsulta.objects.filter(pk=consulta.pk).update(**update_kwargs)

            if status == "autorizado" and consulta.data_agendada:
                if consulta.data_agendada < timezone.localdate():
                    resultado = random.choices(self.RESULTADOS, weights=[0.55, 0.35, 0.10])[0]
                    RegulacaoConsulta.objects.filter(pk=consulta.pk).update(
                        resultado_atendimento=resultado,
                        resultado_em=timezone.now() - timedelta(days=random.randint(0, 20)),
                    )

            criados += 1

        return {"criados": criados, "status": status_counter}

    def _gerar_numero_pedido(self, prefixo, ubs_id):
        sufixo = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{prefixo}-{ubs_id:03d}-{sufixo}"

    def _slugify(self, value):
        normalized = (
            value.lower()
            .replace(" ", "-")
            .replace("á", "a")
            .replace("ã", "a")
            .replace("â", "a")
            .replace("é", "e")
            .replace("ê", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ô", "o")
            .replace("ú", "u")
            .replace("ç", "c")
        )
        return normalized
