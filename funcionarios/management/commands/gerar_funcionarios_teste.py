import random

from django.core.management.base import BaseCommand

from funcionarios.models import Funcionario

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

PHONES = [
    "(34) 99999-1001", "(34) 99999-1002", "(34) 99999-1003", "(34) 99999-1004",
    "(34) 99999-1005", "(34) 99999-1006", "(34) 99999-1007", "(34) 99999-1008",
]

CARGOS = [choice[0] for choice in Funcionario.cargos]


def gerar_cpf(unicos):
    """Gera um CPF aleatório (11 dígitos) garantindo que não repita."""
    while True:
        cpf = "".join(str(random.randint(0, 9)) for _ in range(11))
        if cpf not in unicos:
            unicos.add(cpf)
            return cpf


class Command(BaseCommand):
    help = "Cria funcionários fictícios para testes em ambiente de desenvolvimento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quantidade",
            type=int,
            default=100,
            help="Quantidade total de funcionários desejados após a execução (padrão: 100).",
        )

    def handle(self, *args, **options):
        alvo = max(1, options.get("quantidade") or 100)
        existentes = Funcionario.objects.count()
        faltam = max(alvo - existentes, 0)

        if faltam == 0:
            self.stdout.write(self.style.WARNING(
                f"Já existem {existentes} funcionários cadastrados. Nenhum novo registro foi criado."
            ))
            return

        nomes_usados = set(Funcionario.objects.values_list("nome", flat=True))
        cpfs_usados = set(filter(None, Funcionario.objects.values_list("cpf", flat=True)))

        criados = []
        for _ in range(faltam):
            base_nome = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            nome = base_nome
            sufixo = 2
            while nome in nomes_usados:
                nome = f"{base_nome} #{sufixo}"
                sufixo += 1
            nomes_usados.add(nome)

            funcionario = Funcionario(
                nome=nome,
                cpf=gerar_cpf(cpfs_usados),
                cargo=random.choice(CARGOS),
                telefone=random.choice(PHONES),
            )
            funcionario.save()
            criados.append(funcionario.nome)

        total_final = existentes + len(criados)
        self.stdout.write(self.style.SUCCESS(
            f"Funcionários criados: {len(criados)}. Total atual: {total_final}."
        ))
        if criados:
            exemplos = ", ".join(criados[:5])
            if len(criados) > 5:
                exemplos += ", ..."
            self.stdout.write(f"Exemplos: {exemplos}")
