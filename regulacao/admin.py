from django.contrib import admin
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame

@admin.register(UBS)
class UBSAdmin(admin.ModelAdmin):
    list_display = ['nome', 'responsavel', 'telefone', 'ativa', 'criado_em']
    list_filter = ['ativa', 'criado_em']
    search_fields = ['nome', 'responsavel', 'endereco']
    list_editable = ['ativa']

@admin.register(MedicoSolicitante)
class MedicoSolicitanteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'crm', 'especialidade', 'ubs_padrao', 'ativo', 'criado_em']
    list_filter = ['ativo', 'especialidade', 'ubs_padrao', 'criado_em']
    search_fields = ['nome', 'crm', 'especialidade']
    list_editable = ['ativo']

@admin.register(TipoExame)
class TipoExameAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'valor', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'codigo', 'codigo_sus', 'descricao']
    list_editable = ['ativo']

@admin.register(RegulacaoExame)
class RegulacaoExameAdmin(admin.ModelAdmin):
    list_display = ['numero_protocolo', 'paciente', 'tipo_exame', 'status', 'prioridade', 'ubs_solicitante', 'medico_solicitante', 'data_solicitacao', 'data_regulacao']
    list_filter = ['status', 'prioridade', 'ubs_solicitante', 'medico_solicitante', 'data_solicitacao', 'data_regulacao']
    search_fields = ['numero_protocolo', 'paciente__nome', 'paciente__cpf', 'tipo_exame__nome']
    readonly_fields = ['numero_protocolo', 'data_solicitacao', 'data_regulacao']
    
    fieldsets = (
        ('Informações da Solicitação', {
            'fields': ('numero_protocolo', 'paciente', 'tipo_exame', 'prioridade', 'ubs_solicitante', 'medico_solicitante', 'observacoes', 'data_solicitacao')
        }),
        ('Regulação', {
            'fields': ('status', 'regulador', 'justificativa', 'data_regulacao'),
            'classes': ('collapse',)
        }),
    )
