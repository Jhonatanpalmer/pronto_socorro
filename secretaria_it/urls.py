"""
URL configuration for secretaria_it project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

'''
from django.contrib import admin
from django.urls import path
from viagens.views import ViagemListView, ViagemCreateView, ViagemUpdateView
from pacientes.views import PacienteListView, PacienteCreateView, PacienteUpdateView, PacienteDeleteView
from pacientes import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #### Listar e Gerenciar Viagens ####
    path('', ViagemListView.as_view(), name='viagem-list'),
    path('nova/', ViagemCreateView.as_view(), name='viagem-create'),
    path('editar/<int:pk>/', ViagemUpdateView.as_view(), name='viagem-edit'),
    #### Fim Listar e Gerenciar Viagens ####
    
    #### URLs de Pacientes ###
   path("", PacienteListView.as_view(), name="paciente_list"),
    path("novo/", PacienteCreateView.as_view(), name="paciente_create"),
    path("editar/<int:pk>/", PacienteUpdateView.as_view(), name="paciente_update"),
    path("deletar/<int:pk>/", PacienteDeleteView.as_view(), name="paciente_delete")
]
'''

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # URLs do app Viagens
    path('', include('viagens.urls')),

    # URLs do app Pacientes
    path('pacientes/', include('pacientes.urls')),
    
    # URLs do app TFD
    path('tfd/', include('tfd.urls')),
]
