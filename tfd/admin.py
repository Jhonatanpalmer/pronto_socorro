from django.contrib import admin

from .models import TFD
from .templatetags.currency_filters import br_currency


@admin.register(TFD)
class TFDAdmin(admin.ModelAdmin):
	list_display = ('paciente_nome', 'data_inicio', 'cidade_destino', 'numero_diarias', 'valor_diaria_display', 'valor_beneficio_display', 'valor_total_display', 'secretario_autorizado')
	search_fields = ('paciente_nome', 'paciente_cpf', 'paciente_cns')
	list_filter = ('data_inicio', 'secretario_autorizado')
	readonly_fields = ('valor_total', 'criado_em', 'atualizado_em', 'autorizado_em')

	def valor_diaria_display(self, obj):
		return br_currency(obj.valor_diaria)
	valor_diaria_display.short_description = 'Valor diária'

	def valor_beneficio_display(self, obj):
		return br_currency(obj.valor_beneficio)
	valor_beneficio_display.short_description = 'Valor do benefício'

	def valor_total_display(self, obj):
		return br_currency(obj.valor_total)
	valor_total_display.short_description = 'Valor total'
