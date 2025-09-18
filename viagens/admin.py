from django.contrib import admin
from .models import Viagem

class ViagemAdmin(admin.ModelAdmin):
    list_display = (
        'paciente', 'endereco_paciente', 'destino', 'data_viagem', 'hora_saida',
        'veiculo', 'motorista', 'hospital', 'tipo_atendimento', 'acompanhante', 'status'
    )
    list_filter = ('status', 'hospital')
    search_fields = ('paciente__nome', 'destino', 'hospital', 'acompanhante')
    fields = (
        'paciente', 'endereco_paciente', 'destino', 'data_viagem', 'hora_saida',
        'veiculo', 'motorista', 'hospital', 'tipo_atendimento', 'acompanhante',
        'observacoes', 'status'
    )

admin.site.register(Viagem, ViagemAdmin)
