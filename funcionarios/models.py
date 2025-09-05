from django.db import models

class Funcionario(models.Model):
    cargos = [ 
     ('medico', 'Medico'),
     ('administrativo', 'Administrativo'),
     ('motorista', 'Motorista'),
     ('ti', 'Técnico de Informática'),   
    ]
    
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, blank=True)
    cargo = models.CharField(max_length=20, choices=cargos)
    #registro_profissional = models.CharField(max_length=50, blank=True, null=True)  
    telefone = models.CharField(max_length=20, blank=True) 
    
    
    