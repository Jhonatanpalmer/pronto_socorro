from django.urls import path
from . import views

urlpatterns = [
    path('', views.TFDListView.as_view(), name='tfd-list'),
    path('nova/', views.TFDCreateView.as_view(), name='tfd-create'),
    path('editar/<int:pk>/', views.TFDUpdateView.as_view(), name='tfd-update'),
    path('deletar/<int:pk>/', views.TFDDeleteView.as_view(), name='tfd-delete'),
    path('<int:pk>/imprimir/', views.TFDPrintView.as_view(), name='tfd-print'),  # ✅ Nova URL
    path('buscar-paciente-cpf/', views.buscar_paciente_por_cpf, name='tfd-buscar-paciente-cpf'),
    path('buscar-paciente-nome/', views.buscar_paciente_por_nome, name='tfd-buscar-paciente-nome'),
    path('<int:pk>/', views.TFDDetailView.as_view(), name='tfd-detail'),
]
