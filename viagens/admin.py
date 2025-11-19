from django.contrib import admin
from .models import Viagem, TipoAtendimentoViagem, HospitalAtendimento

class ViagemAdmin(admin.ModelAdmin):
    list_display = (
        'paciente', 'endereco_paciente', 'destino', 'data_viagem', 'hora_saida',
        'veiculo', 'motorista_nome', 'hospital', 'tipo_atendimento', 'acompanhante', 'status'
    )
    list_filter = ('status', 'hospital', 'tipo_atendimento')
    search_fields = ('paciente__nome', 'destino', 'hospital', 'tipo_atendimento', 'acompanhante')
    fields = (
        'paciente', 'endereco_paciente', 'destino', 'data_viagem', 'hora_saida',
        'veiculo', 'motorista', 'hospital', 'tipo_atendimento', 'acompanhante',
        'observacoes', 'status'
    )

admin.site.register(Viagem, ViagemAdmin)


@admin.register(TipoAtendimentoViagem)
class TipoAtendimentoViagemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'atualizado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')


@admin.register(HospitalAtendimento)
class HospitalAtendimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'atualizado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
