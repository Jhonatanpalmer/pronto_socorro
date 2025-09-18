from django.db import models
from pacientes.models import Paciente
from veiculos.models import Veiculo
from datetime import time, timedelta, datetime


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
    motorista = models.CharField(max_length=150, default="Não informado")
    hospital = models.CharField(max_length=200, default="Não informado")
    tipo_atendimento = models.CharField(max_length=100, default="Não informado")
    acompanhante = models.CharField(max_length=150, blank=True, default="")  # agora é nome
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.paciente} → {self.destino} ({self.data_viagem})"


class HistoricoPaciente(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    viagem = models.ForeignKey(Viagem, on_delete=models.CASCADE)
    descricao = models.TextField()
    data_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Histórico {self.paciente} - {self.data_registro.strftime('%d/%m/%Y')}"
