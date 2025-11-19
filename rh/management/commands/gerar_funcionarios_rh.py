import random
import unicodedata
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from rh.models import FuncionarioRH

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

SETORES = [
    "Secretaria de Saúde", "Pronto Atendimento", "Farmácia Municipal",
    "Samu", "Laboratório", "Departamento Administrativo", "Recursos Humanos",
    "TI", "Transporte Sanitário", "Vigilância Epidemiológica",
]

CARGOS = [
    "Médico Plantonista", "Enfermeiro", "Técnico de Enfermagem", "Recepcionista",
    "Motorista", "Assistente Administrativo", "Farmacêutico", "Técnico em TI",
    "Fisioterapeuta", "Psicólogo(a)",
]

DOMINIO_EMAIL = "iturama.mg.gov.br"


def normalize_slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto)
    base = "".join(ch for ch in base if ch.isascii())
    base = base.lower()
    return "".join(ch for ch in base if ch.isalnum())


def gerar_cpf(unicos: set[str]) -> str:
    while True:
        cpf = "".join(str(random.randint(0, 9)) for _ in range(11))
        if cpf not in unicos:
            unicos.add(cpf)
            return cpf


def gerar_rg() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(9))


def random_date(start_year: int, end_year: int) -> date:
    inicio = date(start_year, 1, 1)
    fim = date(end_year, 12, 31)
    delta = (fim - inicio).days
    return inicio + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Cria funcionários de teste no módulo de RH para uso em desenvolvimento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quantidade",
            type=int,
            default=100,
            help="Quantidade total de funcionários do RH desejada ao final da execução (padrão: 100).",
        )

    def handle(self, *args, **options):
        alvo = max(1, options.get("quantidade") or 100)
        existentes = FuncionarioRH.objects.count()
        faltam = max(alvo - existentes, 0)

        if faltam == 0:
            self.stdout.write(self.style.WARNING(
                f"Já existem {existentes} funcionários cadastrados no RH. Nenhum novo registro foi criado."
            ))
            return

        nomes_usados = set(FuncionarioRH.objects.values_list("nome", flat=True))
        cpfs_usados = set(FuncionarioRH.objects.values_list("cpf", flat=True))
        emails_usados = set(FuncionarioRH.objects.values_list("email", flat=True))
        nome_combinacoes = set()

        criados = []
        for _ in range(faltam):
            # Garante combinações únicas de nome + sobrenome. Quando esgotar, gera nomes compostos.
            tentativa = 0
            while True:
                tentativa += 1
                nome_dado = random.choice(FIRST_NAMES)
                sobrenome = random.choice(LAST_NAMES)
                combinacao = (nome_dado, sobrenome)
                if combinacao not in nome_combinacoes or tentativa > 50:
                    nome_combinacoes.add(combinacao)
                    break

            if tentativa > 50:
                sobrenome_extra = random.choice(LAST_NAMES)
                nome = f"{nome_dado} {sobrenome} {sobrenome_extra}"
            else:
                nome = f"{nome_dado} {sobrenome}"

            while nome in nomes_usados:
                nome = f"{nome} {random.choice(LAST_NAMES)}"
            nomes_usados.add(nome)

            cpf = gerar_cpf(cpfs_usados)
            rg = gerar_rg()
            data_nascimento = random_date(1960, 2002)
            telefone = f"(34) 9{random.randint(4000, 9999):04d}-{random.randint(1000, 9999):04d}"

            email_base = normalize_slug(nome.split()[0] + sobrenome) or f"func{random.randint(1000,9999)}"
            email = f"{email_base}@{DOMINIO_EMAIL}"
            sequencia = 2
            while email in emails_usados:
                email = f"{email_base}{sequencia}@{DOMINIO_EMAIL}"
                sequencia += 1
            emails_usados.add(email)

            cargo = random.choice(CARGOS)
            situacao = random.choices(
                [FuncionarioRH.Situacao.ATIVO, FuncionarioRH.Situacao.INATIVO],
                weights=[0.8, 0.2],
                k=1,
            )[0]
            vinculo = random.choice(list(FuncionarioRH.Vinculo))

            data_admissao = random_date(2005, 2024)
            data_desligamento = None
            if situacao == FuncionarioRH.Situacao.INATIVO:
                delta = random.randint(30, 365 * 3)
                data_desligamento = data_admissao + timedelta(days=delta)
                if data_desligamento > date.today():
                    data_desligamento = date.today()

            cep = f"38{random.randint(20000, 29999):05d}"
            endereco = f"Rua {random.choice(LAST_NAMES)}"
            numero = str(random.randint(10, 999))
            bairro = random.choice([
                "Centro", "Jardim Primavera", "Vila Esperança", "Nossa Senhora Aparecida",
                "Jardim América", "Vila Nova"
            ])
            cidade = "Iturama"
            uf = "MG"
            setor = random.choice(SETORES)

            funcionario = FuncionarioRH(
                nome=nome,
                cpf=cpf,
                rg=rg,
                data_nascimento=data_nascimento,
                telefone=telefone,
                email=email,
                cargo=cargo,
                situacao=situacao,
                vinculo=vinculo,
                data_admissao=data_admissao,
                data_desligamento=data_desligamento,
                cep=cep,
                endereco=endereco,
                numero=numero,
                bairro=bairro,
                cidade=cidade,
                uf=uf,
                setor_lotacao=setor,
                observacoes="Gerado automaticamente para testes.",
            )
            funcionario.save()
            criados.append(funcionario.nome)

        total_final = existentes + len(criados)
        self.stdout.write(self.style.SUCCESS(
            f"Funcionários (RH) criados: {len(criados)}. Total atual: {total_final}."
        ))
        if criados:
            exemplos = ", ".join(criados[:5])
            if len(criados) > 5:
                exemplos += ", ..."
            self.stdout.write(f"Exemplos: {exemplos}")
