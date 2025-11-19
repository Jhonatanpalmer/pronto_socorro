from django.contrib import admin
from .models import Motorista, ViagemMotorista
from .forms import MotoristaForm

@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "cpf", "cnh_numero", "situacao")
    search_fields = ("nome_completo", "cpf", "cnh_numero")
    list_filter = ("situacao",)
    form = MotoristaForm

@admin.register(ViagemMotorista)
class ViagemMotoristaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "motorista", "data_inicio", "data_fim", "origem", "destino")
    search_fields = ("codigo", "motorista__nome_completo", "origem", "destino")
    list_filter = ("data_inicio", "data_fim")
