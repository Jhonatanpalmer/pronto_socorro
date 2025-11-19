from django.db import models
from pacientes.models import Paciente
from veiculos.models import Veiculo
from datetime import timedelta, datetime


class TipoAtendimentoViagem(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    descricao = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Tipo de Atendimento'
        verbose_name_plural = 'Tipos de Atendimento'

    def __str__(self):
        return self.nome


class HospitalAtendimento(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    descricao = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Hospital de Atendimento'
        verbose_name_plural = 'Hospitais de Atendimento'

    def __str__(self):
        return self.nome


class DestinoViagem(models.Model):
    nome_cidade = models.CharField(max_length=120)
    uf = models.CharField(max_length=2)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("nome_cidade", "uf")
        ordering = ["nome_cidade", "uf"]
        verbose_name = "Cidade de Destino"
        verbose_name_plural = "Cidades de Destino"

    def __str__(self):
        return f"{self.nome_cidade}/{self.uf}"


def gerar_horarios():
    """Gera opções de horários de 30 em 30 minutos (00:00 até 23:30)."""
    horarios = []
    hora = datetime.strptime("00:00", "%H:%M")
    fim = datetime.strptime("23:30", "%H:%M")
    while hora <= fim:
        horarios.append((hora.time(), hora.strftime("%H:%M")))
        hora += timedelta(minutes=30)
    return horarios


class Viagem(models.Model):
    STATUS = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("cancelado", "Cancelado"),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    endereco_paciente = models.CharField(max_length=300, default="Não informado")
    destino = models.CharField(max_length=200)
    data_viagem = models.DateField()
    hora_saida = models.TimeField(choices=gerar_horarios(), null=True, blank=True)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.SET_NULL, null=True, blank=True)
    # Relacionamento definitivo com Motorista
    motorista = models.ForeignKey('motorista.Motorista', on_delete=models.SET_NULL, null=True, blank=True, related_name='viagens_agendadas')
    hospital = models.CharField(max_length=200, default="Não informado")
    tipo_atendimento = models.CharField(max_length=100, default="Não informado")
    acompanhante = models.CharField(max_length=150, blank=True, default="")  # agora é nome
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    observacoes = models.TextField(blank=True)

    def __str__(self):
        destino_label = self.destino or "Destino não informado"
        return f"{self.paciente} → {destino_label} ({self.data_viagem})"

    @property
    def motorista_nome(self):
        """Retorna o nome do motorista preferindo o FK quando disponível."""
        if self.motorista_id and getattr(self.motorista, 'nome_completo', None):
            return self.motorista.nome_completo
        return ''


class HistoricoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    viagem = models.ForeignKey(Viagem, on_delete=models.CASCADE)
    descricao = models.TextField()
    data_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Histórico {self.paciente} - {self.data_registro.strftime('%d/%m/%Y')}"
