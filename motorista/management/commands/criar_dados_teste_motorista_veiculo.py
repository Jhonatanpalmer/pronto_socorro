import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from motorista.models import Motorista
from veiculos.models import Veiculo


class Command(BaseCommand):
    help = "Cria motoristas e veículos (ônibus, motos etc.) para testes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--motoristas",
            type=int,
            default=20,
            help="Quantidade de motoristas de teste a criar (padrão: 20).",
        )
        parser.add_argument(
            "--veiculos",
            type=int,
            default=30,
            help="Quantidade de veículos de teste a criar (padrão: 30).",
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

        qtd_motoristas = max(0, options["motoristas"])
        qtd_veiculos = max(0, options["veiculos"])

        created_motoristas = self._criar_motoristas(qtd_motoristas)
        created_veiculos = self._criar_veiculos(qtd_veiculos)

        self.stdout.write(self.style.SUCCESS("Criação de dados de teste concluída."))
        self.stdout.write(f"Motoristas criados: {created_motoristas}")
        self.stdout.write(f"Veículos criados: {created_veiculos}")

    # ----------------- helpers -----------------

    def _criar_motoristas(self, quantidade: int) -> int:
        if quantidade <= 0:
            return 0

        created = 0
        base_nomes = [
            "João Silva", "Maria Souza", "Carlos Pereira", "Ana Oliveira",
            "Pedro Santos", "Fernanda Lima", "Ricardo Alves", "Juliana Costa",
            "Marcos Rocha", "Patrícia Gomes", "Lucas Ribeiro", "Aline Castro",
            "Eduardo Moreira", "Camila Duarte", "Rafael Faria", "Bianca Mendes",
        ]
        today = timezone.localdate()

        for idx in range(quantidade):
            nome = random.choice(base_nomes)
            # CPF fictício, apenas para testes (sem validação real nesta geração)
            cpf_digitos = f"{random.randint(0, 99999999999):011d}"
            cpf = f"{cpf_digitos[:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:]}"

            # Evitar conflito de CPF único: se já existir, pula
            if Motorista.objects.filter(cpf=cpf_digitos).exists() or Motorista.objects.filter(cpf=cpf).exists():
                continue

            ano_nasc = random.randint(1960, 2000)
            dia_ano = random.randint(1, 365)
            data_nasc = date(ano_nasc, 1, 1) + timedelta(days=dia_ano - 1)

            motorista = Motorista(
                nome_completo=nome,
                cpf=cpf,
                rg=str(random.randint(1000000, 99999999)),
                data_nascimento=data_nasc,
                cnh_numero=str(random.randint(10000000000, 99999999999)),
                cnh_categoria=random.choice(["A", "B", "C", "D", "E", "AB", "AD"]),
                cnh_validade=today + timedelta(days=random.randint(180, 365 * 5)),
                endereco=f"Rua {random.randint(1, 300)}, Bairro Centro",
                telefone=f"(34) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                email=f"motorista{random.randint(1,9999)}@teste.com",
                matricula=f"MT{random.randint(1000,9999)}",
                data_admissao=today - timedelta(days=random.randint(30, 365 * 5)),
                situacao=random.choice(["ativo", "inativo"]),
                escala_trabalho=random.choice(["Diurno", "Noturno", "Plantão 12x36"]),
            )
            motorista.save()
            created += 1
        return created

    def _criar_veiculos(self, quantidade: int) -> int:
        if quantidade <= 0:
            return 0

        created = 0
        tipos = ["onibus", "van", "carro", "moto", "caminhonete", "ambulancia"]
        modelos_onibus = ["Marcopolo Viaggio", "Comil Campione", "Neobus Spectrum"]
        modelos_carro = ["Onix", "Gol", "Corolla", "Uno", "Fiesta"]
        modelos_moto = ["CG 160", "Biz 125", "YBR 150"]

        for idx in range(quantidade):
            tipo = random.choice(tipos)
            if tipo in ("onibus", "van"):
                modelo = random.choice(modelos_onibus)
            elif tipo == "moto":
                modelo = random.choice(modelos_moto)
            else:
                modelo = random.choice(modelos_carro)

            placa = self._gerar_placa()
            if Veiculo.objects.filter(placa=placa).exists():
                continue

            veiculo = Veiculo(
                placa=placa,
                modelo=modelo,
                tipo=tipo,
                capacidade=random.randint(2, 50) if tipo in ("onibus", "van") else random.randint(1, 7),
                combustivel=random.choice(["alcool", "gasolina", "diesel", "total_flex"]),
            )
            veiculo.save()
            created += 1
        return created

    def _gerar_placa(self) -> str:
        # Formato simples AAA-1234 / ABC1D23 etc. para testes
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        numeros = "0123456789"
        if random.random() < 0.5:
            # Formato antigo
            return "{}{}{}-{}{}{}{}".format(
                random.choice(letras),
                random.choice(letras),
                random.choice(letras),
                random.choice(numeros),
                random.choice(numeros),
                random.choice(numeros),
                random.choice(numeros),
            )
        # Formato Mercosul simplificado ABC1D23
        return "{}{}{}{}{}{}{}".format(
            random.choice(letras),
            random.choice(letras),
            random.choice(letras),
            random.choice(numeros),
            random.choice(letras),
            random.choice(numeros),
            random.choice(numeros),
        )
