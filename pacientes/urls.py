from django.urls import path
from .views import (
    PacienteListView,
    PacienteCreateView,
    PacienteUpdateView,
    PacienteDeleteView,
    paciente_autocomplete,
    PacienteHistoricoView,
)

urlpatterns = [
    path('', PacienteListView.as_view(), name='paciente_list'),
    path('novo/', PacienteCreateView.as_view(), name='paciente_create'),
    path('editar/<int:pk>/', PacienteUpdateView.as_view(), name='paciente_update'),
    path('deletar/<int:pk>/', PacienteDeleteView.as_view(), name='paciente_delete'),
    path('autocomplete/', paciente_autocomplete, name='paciente_autocomplete'),
    path('<int:pk>/historico/', PacienteHistoricoView.as_view(), name='paciente_historico'),
]
