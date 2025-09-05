from django.db import models
from pacientes.models import Paciente
from veiculos.models import Veiculo
from datetime import time

class Viagem(models.Model):
    TIPOS_TRANSPORTE = [
        ("oficial", "Veículo Oficial"),
        ("onibus", "Ônibus"),
        ("carro_proprio", "Carro Próprio"),
    ]

    STATUS = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("cancelado", "Cancelado"),
    ]
    
    horario_saida = [
    (time(2, 0), '02:00'),
    (time(3, 0), '03:00'),
]
    
    cidade_destino = [
        ('Uberaba', 'Uberaba'),
        ('Fernandopolis', 'Fernandopolis'),
        ('Sao Jose do Rio Preto', 'Sao Jose do Rio Preto'),
        ('Barretos', 'Barretos'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    destino = models.CharField(max_length=200, choices=cidade_destino)
    data_viagem = models.DateField()
    hora_saida = models.TimeField(choices=horario_saida, null=True, blank=True)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_transporte = models.CharField(max_length=30, choices=TIPOS_TRANSPORTE)
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
