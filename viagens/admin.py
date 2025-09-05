from django.contrib import admin


from .models import Viagem, HistoricoPaciente

@admin.register(Viagem)
class ViagemAdmin(admin.ModelAdmin):
    list_display = ("paciente", "destino", "data_viagem", "tipo_transporte", "status")
    search_fields = ("paciente__nome", "destino")
    list_filter = ("status", "tipo_transporte", "data_viagem")

@admin.register(HistoricoPaciente)
class HistoricoPacienteAdmin(admin.ModelAdmin):
    list_display = ("paciente", "viagem", "data_registro")
    search_fields = ("paciente__nome", "viagem__destino")
    list_filter = ("data_registro",)
