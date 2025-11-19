from django.urls import path
from . import views

urlpatterns = [
    path('abastecimentos/', views.abastecimento_list, name='abastecimento-list'),
    path('abastecimentos/novo/', views.abastecimento_create, name='abastecimento-create'),
    path('abastecimentos/<int:pk>/imprimir/', views.abastecimento_print, name='abastecimento-print'),
    path('abastecimentos/<int:pk>/editar/', views.abastecimento_update, name='abastecimento-update'),
    path('abastecimentos/<int:pk>/excluir/', views.abastecimento_delete, name='abastecimento-delete'),
    path('abastecimentos/<int:pk>/restaurar/', views.abastecimento_restore, name='abastecimento-restore'),
    # Manutenções
    path('manutencoes/', views.manutencao_list, name='manutencao-list'),
    path('manutencoes/nova/', views.manutencao_create, name='manutencao-create'),
    path('manutencoes/<int:pk>/', views.manutencao_detail, name='manutencao-detail'),
    path('manutencoes/<int:pk>/editar/', views.manutencao_update, name='manutencao-update'),
    path('manutencoes/<int:pk>/concluir/', views.manutencao_finalize, name='manutencao-finalize'),
    path('manutencoes/<int:pk>/imprimir/', views.manutencao_print, name='manutencao-print'),
    # Locais de manutenção
    path('locais-manutencao/', views.local_manutencao_list, name='local-manutencao-list'),
    path('locais-manutencao/novo/', views.local_manutencao_create, name='local-manutencao-create'),
    path('locais-manutencao/<int:pk>/editar/', views.local_manutencao_update, name='local-manutencao-update'),
    path('locais-manutencao/<int:pk>/excluir/', views.local_manutencao_delete, name='local-manutencao-delete'),
    # Veículos
    path('veiculos/', views.veiculo_list, name='veiculo-list'),
    path('veiculos/novo/', views.veiculo_create, name='veiculo-create'),
    path('veiculos/<int:pk>/editar/', views.veiculo_update, name='veiculo-update'),
    path('veiculos/<int:pk>/excluir/', views.veiculo_delete, name='veiculo-delete'),
]
