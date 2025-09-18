from django.urls import path
from .views import ViagemListView, ViagemCreateView, ViagemUpdateView, ViagemDeleteView

urlpatterns = [
    path('', ViagemListView.as_view(), name='viagem-list'),
    path('nova/', ViagemCreateView.as_view(), name='viagem-create'),
    path('editar/<int:pk>/', ViagemUpdateView.as_view(), name='viagem-edit'),
    path('deletar/<int:pk>/', ViagemDeleteView.as_view(), name='viagem-delete'),
]
