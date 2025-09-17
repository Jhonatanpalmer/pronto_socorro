from django.db import models
from django.core.exceptions import ValidationError

def validate_cpf(value):
    """Valida CPF brasileiro (11 dígitos e dígitos verificadores)"""
    if not value:
        return  # permite campo vazio
    cpf = ''.join(filter(str.isdigit, value))
    if len(cpf) != 11:
        raise ValidationError("CPF deve ter 11 dígitos.")

    # Dígito verificador
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = ((sum1 * 10) % 11) % 10
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = ((sum2 * 10) % 11) % 10

    if d1 != int(cpf[9]) or d2 != int(cpf[10]):
        raise ValidationError("CPF inválido.")

class Paciente(models.Model):
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=11, blank=True, null=True, unique=True, validators=[validate_cpf])
    cns = models.CharField(max_length=15, blank=True, null=True)
    data_nascimento = models.DateField()
    endereco = models.TextField(max_length=30)
    telefone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nome
