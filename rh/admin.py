from django.contrib import admin
from .models import FuncionarioRH, AtestadoMedico


@admin.register(FuncionarioRH)
class FuncionarioRHAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'cargo', 'situacao', 'vinculo', 'data_admissao')
    list_filter = ('situacao', 'vinculo')
    search_fields = ('nome', 'cpf', 'cargo')


@admin.register(AtestadoMedico)
class AtestadoMedicoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data_inicio', 'data_fim', 'dias', 'cid', 'criado_em')
    list_filter = ('data_inicio', 'data_fim')
    search_fields = ('funcionario__nome', 'cid', 'medico', 'crm')
