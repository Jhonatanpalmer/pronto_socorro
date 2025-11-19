from django.conf import settings
from django.db import models
from django.utils import timezone
from funcionarios.models import Funcionario


class Veiculo(models.Model):
    TIPO_VEICULO_CHOICES = (
        ("carro", "Carro"),
        ("moto", "Moto"),
        ("caminhonete", "Caminhonete"),
        ("ambulancia", "Ambulância"),
        ("van", "Van"),
        ("onibus", "Ônibus"),
        ("caminhao", "Caminhão"),
        ("outro", "Outro"),
    )

    COMBUSTIVEL_CHOICES = (
        ("alcool", "Álcool"),
        ("gasolina", "Gasolina"),
        ("diesel", "Diesel"),
        ("total_flex", "Total Flex"),
    )

    placa = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_VEICULO_CHOICES, default="carro")
    capacidade = models.IntegerField(default=4)
    combustivel = models.CharField(max_length=12, choices=COMBUSTIVEL_CHOICES, default="gasolina")
    motorista = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"cargo": "motorista"},
        related_name="veiculos",
    )

    def __str__(self):
        return f"{self.modelo} - {self.placa}"


class Abastecimento(models.Model):
    COMBUSTIVEL_CHOICES = (
        ("alcool", "Álcool"),
        ("gasolina", "Gasolina"),
        ("diesel", "Diesel"),
    )

    TIPO_VEICULO_CHOICES = Veiculo.TIPO_VEICULO_CHOICES

    motorista = models.ForeignKey(
        'motorista.Motorista',
        on_delete=models.PROTECT,
        related_name="abastecimentos",
    )
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name="abastecimentos")
    tipo_veiculo = models.CharField(max_length=20, choices=TIPO_VEICULO_CHOICES)
    tipo_combustivel = models.CharField(max_length=10, choices=COMBUSTIVEL_CHOICES)
    local_abastecimento = models.CharField(max_length=100)
    data_hora = models.DateTimeField(default=timezone.now)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="abastecimentos_registrados",
    )
    excluido_em = models.DateTimeField(null=True, blank=True)
    excluido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="abastecimentos_excluidos",
    )

    class Meta:
        ordering = ["-data_hora", "-id"]

    @property
    def esta_excluido(self) -> bool:
        return self.excluido_em is not None

    def __str__(self):
        return f"{self.veiculo.placa} - {self.get_tipo_combustivel_display()} em {self.data_hora:%d/%m/%Y %H:%M}"


class LocalManutencao(models.Model):
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=120)
    responsavel = models.CharField(max_length=120, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Local de Manutenção"
        verbose_name_plural = "Locais de Manutenção"

    def __str__(self):
        cidade = f" - {self.cidade}" if self.cidade else ""
        return f"{self.nome}{cidade}"


class ManutencaoVeiculo(models.Model):
    STATUS_CHOICES = (
        ("pendente", "Pendente"),
        ("em_andamento", "Em andamento"),
        ("concluida", "Concluída"),
    )

    TIPO_CHOICES = (
        ("preventiva", "Preventiva"),
        ("corretiva", "Corretiva"),
        ("revisao", "Revisão"),
        ("outro", "Outro"),
    )

    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name="manutencoes")
    local = models.ForeignKey(LocalManutencao, null=True, blank=True, on_delete=models.SET_NULL, related_name="manutencoes")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="corretiva")
    data_envio = models.DateField()
    data_retorno = models.DateField(null=True, blank=True)
    descricao_problema = models.TextField()
    servicos_realizados = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_envio", "-id"]
        verbose_name = "Manutenção de Veículo"
        verbose_name_plural = "Manutenções de Veículos"

    def __str__(self):
        return f"{self.veiculo.placa} - {self.get_status_display()}"

    @property
    def em_aberto(self) -> bool:
        return self.status != "concluida" or self.data_retorno is None

