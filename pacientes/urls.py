from django.urls import path
from .views import PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView

urlpatterns = [
    path('', PacienteListView.as_view(), name='paciente_list'),
    path('novo/', PacienteCreateView.as_view(), name='paciente_create'),
    path('editar/<int:pk>/', PacienteUpdateView.as_view(), name='paciente_update'),
    path('deletar/<int:pk>/', PacienteDeleteView.as_view(), name='paciente_delete'),
]
