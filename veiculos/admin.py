from django.contrib import admin

from django.contrib import admin
from .models import Veiculo

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "modelo", "motorista", "capacidade")
    search_fields = ("placa", "modelo")
    list_filter = ("motorista",)

