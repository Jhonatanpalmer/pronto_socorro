from django.urls import path
from . import views

urlpatterns = [
    path('funcionarios/', views.funcionario_list, name='rh-funcionario-list'),
    path('funcionarios/novo/', views.funcionario_create, name='rh-funcionario-create'),
    path('funcionarios/<int:pk>/editar/', views.funcionario_update, name='rh-funcionario-update'),
    path('funcionarios/<int:pk>/excluir/', views.funcionario_delete, name='rh-funcionario-delete'),
    # Atestados
    path('atestados/', views.atestado_list, name='rh-atestado-list'),
    path('atestados/novo/', views.atestado_create, name='rh-atestado-create'),
    path('atestados/<int:pk>/editar/', views.atestado_update, name='rh-atestado-update'),
    path('atestados/<int:pk>/remover/', views.atestado_delete, name='rh-atestado-delete'),
    path('atestados/<int:pk>/restaurar/', views.atestado_restore, name='rh-atestado-restore'),
    path('atestados/<int:pk>/imprimir/', views.atestado_print, name='rh-atestado-print'),
    path('api/cid/', views.cid_lookup, name='rh-cid-lookup'),
]
