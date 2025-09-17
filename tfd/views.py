from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import TFD
from .forms import TFDForm

# Lista de TFDs
class TFDListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = TFD
    template_name = 'tfd/tfd_list.html'
    context_object_name = 'tfds'

# Detalhe de um TFD
class TFDDetailView(LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    model = TFD
    template_name = 'tfd/tfd_detail.html'
    context_object_name = 'tfd'

# Criar TFD
class TFDCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')

# Editar TFD
class TFDUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')

# Deletar TFD
class TFDDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = TFD
    template_name = 'tfd/tfd_confirm_delete.html'
    success_url = reverse_lazy('tfd-list')

class TFDPrintView(DetailView):
    model = TFD
    template_name = 'tfd/tfd_print.html'  # Você precisa criar esse template
    context_object_name = 'tfd'