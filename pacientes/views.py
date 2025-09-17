from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Paciente
from .forms import PacienteForm

class PacienteListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = Paciente
    template_name = "pacientes/paciente_list.html"
    context_object_name = "pacientes"
    ordering = ["nome"]

class PacienteCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")

class PacienteUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")

class PacienteDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = Paciente
    template_name = "pacientes/paciente_confirm_delete.html"
    success_url = reverse_lazy("paciente_list")
