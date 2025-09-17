from django.urls import path
from . import views

urlpatterns = [
    path('', views.TFDListView.as_view(), name='tfd-list'),
    path('nova/', views.TFDCreateView.as_view(), name='tfd-create'),
    path('editar/<int:pk>/', views.TFDUpdateView.as_view(), name='tfd-update'),
    path('deletar/<int:pk>/', views.TFDDeleteView.as_view(), name='tfd-delete'),
    path('<int:pk>/imprimir/', views.TFDPrintView.as_view(), name='tfd-print'),  # ✅ Nova URL
    path('<int:pk>/', views.TFDDetailView.as_view(), name='tfd-detail'),
]
