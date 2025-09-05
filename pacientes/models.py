

from django.db import models

class Paciente(models.Model):
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    cns = models.CharField(max_length=15, blank=True, null=True)
    data_nascimento = models.DateField()
    endereco = models.TextField(max_length=30)
    telefone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nome

