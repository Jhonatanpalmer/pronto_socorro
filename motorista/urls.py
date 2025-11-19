from django.urls import path
#from . import views
from motorista import views

urlpatterns = [
    path('motoristas/', views.motorista_home, name='motorista-home'),
    path('motoristas/lista/', views.motorista_list, name='motorista-list'),
    path('motoristas/novo/', views.motorista_create, name='motorista-create'),
    path('motoristas/<int:pk>/editar/', views.motorista_update, name='motorista-update'),
    path('motoristas/<int:pk>/excluir/', views.motorista_delete, name='motorista-delete'),

    path('viagens/', views.viagem_list, name='motorista-viagem-list'),
    path('viagens/imprimir/', views.viagem_print, name='motorista-viagem-print'),
    path('viagens/nova/', views.viagem_create, name='motorista-viagem-create'),
    path('viagens/<int:pk>/editar/', views.viagem_update, name='motorista-viagem-update'),
    path('viagens/<int:pk>/excluir/', views.viagem_delete, name='motorista-viagem-delete'),
    path('viagens/<int:pk>/imprimir/', views.viagem_print_single, name='motorista-viagem-print-single'),

    path('relatorios/', views.relatorios_view, name='motorista-relatorios'),
]
