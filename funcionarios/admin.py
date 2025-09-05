from django.contrib import admin

### Importar o model de Funcionario 
from .models import Funcionario

### Registrar o model de Funcionario no admin
@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'cargo',  'telefone')
    search_fields = ('nome', 'cpf', 'cargo')
    list_filter = ('cargo',)
    ordering = ('nome',)
    fieldsets = (
        (None, {
            'fields': ('nome', 'cpf', 'cargo', 'telefone')
        }),
    )

