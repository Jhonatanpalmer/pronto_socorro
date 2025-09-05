from django.db import models

from django.db import models
from funcionarios.models import Funcionario

class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=100)
    capacidade = models.IntegerField(default=4)
    motorista = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'cargo': 'motorista'}
    )

    def __str__(self):
        return f"{self.modelo} - {self.placa}"

