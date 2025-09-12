from django.contrib import admin

from .models import TFD


@admin.register(TFD)
class TFDAdmin(admin.ModelAdmin):
	list_display = ('paciente_nome', 'data_inicio', 'cidade_destino', 'numero_diarias', 'valor_diaria', 'valor_total', 'secretario_autorizado')
	search_fields = ('paciente_nome', 'paciente_cpf', 'paciente_cns')
	list_filter = ('data_inicio', 'secretario_autorizado')
	readonly_fields = ('valor_total', 'criado_em', 'atualizado_em', 'autorizado_em')
