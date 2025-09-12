from django.urls import path
from . import views

urlpatterns = [
    path('', views.TFDListView.as_view(), name='tfd-list'),
    path('novo/', views.TFDCreateView.as_view(), name='tfd-create'),
    path('<int:pk>/editar/', views.TFDUpdateView.as_view(), name='tfd-edit'),
    path('<int:pk>/', views.TFDDetailView.as_view(), name='tfd-detail'),
    path('<int:pk>/imprimir/', views.TFDPrintView.as_view(), name='tfd-print'),
]
