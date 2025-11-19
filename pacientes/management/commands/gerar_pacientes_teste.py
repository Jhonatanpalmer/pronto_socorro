import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from pacientes.models import Paciente

FIRST_NAMES = [
    "Ana", "João", "Maria", "Pedro", "Lucas", "Mariana", "José", "Paula",
    "Carlos", "Fernanda", "Rafael", "Juliana", "Bruno", "Camila", "Eduardo",
    "Bianca", "Diego", "Larissa", "Felipe", "Isabela", "Gustavo", "Patrícia",
    "André", "Gabriela", "Mateus", "Sofia", "Ricardo", "Luana", "Daniel",
    "Letícia", "Thiago", "Raquel", "Vitor", "Helena", "Leonardo", "Carolina",
    "Renato", "Priscila", "Fábio", "Vanessa",
]

LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Pereira", "Costa", "Rodrigues", "Almeida",
    "Santos", "Carvalho", "Gomes", "Martins", "Araújo", "Ribeiro", "Lima",
    "Barbosa", "Fernandes", "Freitas", "Nascimento", "Teixeira", "Melo",
]

STREET_NAMES = [
    "Rua das Flores", "Avenida Brasil", "Rua São Paulo", "Rua Tiradentes",
    "Rua da Liberdade", "Rua Dom Pedro", "Praça Sete", "Rua das Acácias",
    "Rua Minas Gerais", "Rua Goiás", "Rua Pará", "Rua Acre", "Alameda Paulista",
]

NEIGHBORHOODS = [
    "Centro", "Jardim Primavera", "Nova Iturama", "Vila Esperança",
    "Nossa Senhora Aparecida", "Santa Rita", "Vila Nova", "Jardim América",
]

PHONES = [
    "(34) 99999-1001", "(34) 99999-1002", "(34) 99999-1003", "(34) 99999-1004",
    "(34) 99999-1005", "(34) 99999-1006", "(34) 99999-1007", "(34) 99999-1008",
]


def random_date(start_year: int = 1950, end_year: int = 2015) -> date:
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    delta = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Cria pacientes de teste com dados aleatórios para uso em ambiente de desenvolvimento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quantidade",
            type=int,
            default=50,
            help="Quantidade de pacientes que devem existir ao final da execução (padrão: 50)",
        )

    def handle(self, *args, **options):
        alvo = max(1, options.get("quantidade") or 50)
        existentes = Paciente.objects.count()
        faltam = max(alvo - existentes, 0)
        if faltam == 0:
            self.stdout.write(self.style.WARNING(
                f"Já existem {existentes} pacientes cadastrados. Nenhum novo registro foi criado."
            ))
            return

        criados = []
        usados = set(Paciente.objects.values_list("nome", flat=True))
        for _ in range(faltam):
            # Garante nomes diferentes declarando um sufixo quando necessário
            base = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            nome = base
            tentativa = 1
            while nome in usados:
                tentativa += 1
                nome = f"{base} #{tentativa}"
            usados.add(nome)

            paciente = Paciente(
                nome=nome,
                cns=None,
                data_nascimento=random_date(),
                logradouro=random.choice(STREET_NAMES),
                numero=str(random.randint(10, 999)),
                bairro=random.choice(NEIGHBORHOODS),
                cep=f"38{random.randint(20000, 29999):05d}",
                telefone=random.choice(PHONES),
                nome_mae=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                nome_pai=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            )
            paciente.save()
            criados.append(paciente.nome)

        self.stdout.write(self.style.SUCCESS(
            f"Pacientes criados: {len(criados)}. Total atual: {existentes + len(criados)}."
        ))
        if criados:
            resumo = ", ".join(criados[:5])
            if len(criados) > 5:
                resumo += ", ..."
            self.stdout.write(f"Exemplos: {resumo}")
