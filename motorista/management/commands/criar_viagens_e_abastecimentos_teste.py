import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from motorista.models import Motorista, ViagemMotorista
from veiculos.models import Veiculo, Abastecimento


class Command(BaseCommand):
    help = "Cria viagens de motoristas e abastecimentos de veículos para testes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--viagens",
            type=int,
            default=50,
            help="Quantidade de viagens de teste a criar (padrão: 50).",
        )
        parser.add_argument(
            "--abastecimentos",
            type=int,
            default=80,
            help="Quantidade de abastecimentos de teste a criar (padrão: 80).",
        )
        parser.add_argument(
            "--dias-passado",
            type=int,
            default=90,
            help="Janela em dias para trás a considerar ao sortear datas (padrão: 90).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Seed opcional para geração reprodutível.",
        )

    def handle(self, *args, **options):
        if options.get("seed") is not None:
            random.seed(options["seed"])
        else:
            random.seed()

        qtd_viagens = max(0, options["viagens"])
        qtd_abast = max(0, options["abastecimentos"])
        dias_passado = max(1, options["dias_passado"])

        motoristas = list(Motorista.objects.all())
        veiculos = list(Veiculo.objects.all())
        if not motoristas or not veiculos:
            self.stdout.write(self.style.WARNING("É necessário ter motoristas e veículos cadastrados para gerar viagens/abastecimentos."))
            return

        created_viagens = self._criar_viagens(qtd_viagens, motoristas, veiculos, dias_passado)
        created_abast = self._criar_abastecimentos(qtd_abast, motoristas, veiculos, dias_passado)

        self.stdout.write(self.style.SUCCESS("Criação de viagens e abastecimentos de teste concluída."))
        self.stdout.write(f"Viagens criadas: {created_viagens}")
        self.stdout.write(f"Abastecimentos criados: {created_abast}")

    # ----------------- helpers -----------------

    def _sortear_periodo(self, dias_passado: int):
        today = timezone.localdate()
        delta_inicio = random.randint(0, dias_passado)
        di = today - timedelta(days=delta_inicio)
        duracao = random.randint(0, 5)  # até 6 dias de viagem
        df = di + timedelta(days=duracao)
        return di, df

    def _criar_viagens(self, quantidade: int, motoristas, veiculos, dias_passado: int) -> int:
        if quantidade <= 0:
            return 0
        created = 0
        destinos = [
            "Uberaba/MG",
            "Uberlândia/MG",
            "Belo Horizonte/MG",
            "São Paulo/SP",
            "São José do Rio Preto/SP",
            "Campinas/SP",
            "Goiânia/GO",
            "Ituiutaba/MG",
            "Frutal/MG",
        ]
        motivos = [
            "Consulta especializada",
            "Tratamento oncológico",
            "Exames de alta complexidade",
            "Capacitação de servidores",
            "Transporte de pacientes",
            "Reunião administrativa",
        ]
        for _ in range(quantidade):
            motorista = random.choice(motoristas)
            veiculo = random.choice(veiculos)
            di, df = self._sortear_periodo(dias_passado)
            valor_diaria = random.choice([80, 100, 120, 150, 180])
            qtd_horas = random.choice([0, 0, 0, 2, 4])

            viagem = ViagemMotorista(
                motorista=motorista,
                data_inicio=di,
                data_fim=df,
                origem="Iturama",
                destino=random.choice(destinos),
                veiculo=veiculo,
                valor_unitario_diaria=valor_diaria,
                quantidade_horas_extras=qtd_horas,
                justificativa_horas_extras=(
                    "Plantão estendido." if qtd_horas > 0 else ""
                ),
                motivo_viagem=random.choice(motivos),
                observacoes="Viagem gerada automaticamente para testes.",
            )
            viagem.save()
            created += 1
        return created

    def _criar_abastecimentos(self, quantidade: int, motoristas, veiculos, dias_passado: int) -> int:
        if quantidade <= 0:
            return 0
        created = 0
        locais = [
            "Posto Central",
            "Posto BR 365",
            "Auto Posto Iturama",
            "Posto Avenida",
            "Posto São João",
        ]
        today = timezone.now()
        for _ in range(quantidade):
            motorista = random.choice(motoristas)
            veiculo = random.choice(veiculos)
            dias_atras = random.randint(0, dias_passado)
            hora_offset = random.randint(7, 20)
            data_hora = today - timedelta(days=dias_atras)
            data_hora = data_hora.replace(hour=hora_offset, minute=0, second=0, microsecond=0)

            ab = Abastecimento(
                motorista=motorista,
                veiculo=veiculo,
                tipo_veiculo=veiculo.tipo,
                tipo_combustivel=random.choice(["alcool", "gasolina", "diesel"]),
                local_abastecimento=random.choice(locais),
                data_hora=data_hora,
                observacao="Abastecimento gerado automaticamente para testes.",
            )
            ab.save()
            created += 1
        return created
