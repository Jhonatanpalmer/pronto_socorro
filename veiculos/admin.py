from django.contrib import admin
from .models import Veiculo, Abastecimento, LocalManutencao, ManutencaoVeiculo

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "modelo", "tipo", "combustivel", "motorista", "capacidade")
    search_fields = ("placa", "modelo")
    list_filter = ("tipo", "motorista")


@admin.register(Abastecimento)
class AbastecimentoAdmin(admin.ModelAdmin):
    list_display = ("data_hora", "veiculo", "tipo_veiculo", "motorista", "tipo_combustivel", "local_abastecimento")
    list_filter = ("tipo_veiculo", "tipo_combustivel", "local_abastecimento")
    search_fields = ("veiculo__placa", "veiculo__modelo", "motorista__nome_completo", "local_abastecimento")


@admin.register(LocalManutencao)
class LocalManutencaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cidade", "responsavel", "telefone")
    search_fields = ("nome", "cidade", "responsavel")


@admin.register(ManutencaoVeiculo)
class ManutencaoVeiculoAdmin(admin.ModelAdmin):
    list_display = ("veiculo", "tipo", "status", "data_envio", "data_retorno", "local")
    list_filter = ("status", "tipo", "local")
    search_fields = ("veiculo__placa", "veiculo__modelo", "descricao_problema")

