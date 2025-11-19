from django.contrib import admin
from .models import (
    UBS,
    MedicoSolicitante,
    TipoExame,
    RegulacaoExame,
    LocalAtendimento,
    Especialidade,
    MedicoAmbulatorio,
    AgendaMedica,
)

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

@admin.register(LocalAtendimento)
class LocalAtendimentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'telefone', 'ativo', 'criado_em']
    list_filter = ['ativo', 'tipo', 'criado_em']
    search_fields = ['nome', 'endereco', 'tipo']
    list_editable = ['ativo']


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativa', 'criado_em']
    list_filter = ['ativa']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativa']


@admin.register(MedicoAmbulatorio)
class MedicoAmbulatorioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'crm', 'ativo', 'criado_em']
    list_filter = ['ativo', 'especialidades']
    search_fields = ['nome', 'crm']
    filter_horizontal = ['especialidades']
    list_editable = ['ativo']

@admin.register(AgendaMedica)
class AgendaMedicaAdmin(admin.ModelAdmin):
    list_display = ['medico', 'especialidade', 'dia_semana', 'capacidade', 'ativo']
    list_filter = ['especialidade', 'dia_semana', 'ativo']
    search_fields = ['medico__nome', 'medico__crm', 'especialidade__nome']
