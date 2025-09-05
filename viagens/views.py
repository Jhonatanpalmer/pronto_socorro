from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Viagem
from viagens.forms import ViagemForm


# Listar todas as viagens
class ViagemListView(ListView):
    model = Viagem
    template_name = 'viagens/viagem_list.html'
    context_object_name = 'viagens'


# Criar nova viagem
class ViagemCreateView(CreateView):
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')


# Editar viagem existente
class ViagemUpdateView(UpdateView):
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')
