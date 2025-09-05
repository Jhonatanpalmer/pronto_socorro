from django.contrib import admin

from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "cns", "telefone")
    search_fields = ("nome", "cpf", "cns")
