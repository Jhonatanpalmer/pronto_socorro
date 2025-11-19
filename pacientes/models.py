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
    nome = models.CharField(max_length=150, db_index=True)
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True, validators=[validate_cpf])
    cns = models.CharField(max_length=15, blank=True, null=True, db_index=True)
    data_nascimento = models.DateField(null=True, blank=True)
    # Endereço estruturado
    logradouro = models.CharField(max_length=120, blank=True, help_text='Rua/Avenida/Travessa')
    numero = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=80, blank=True)
    cep = models.CharField(max_length=10, blank=True)
    # Filiação
    nome_mae = models.CharField(max_length=150, blank=True)
    nome_pai = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nome
