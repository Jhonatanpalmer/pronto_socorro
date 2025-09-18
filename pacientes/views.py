from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
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

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Paciente criado com sucesso.")
        return response

class PacienteUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Paciente atualizado com sucesso.")
        return response

class PacienteDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = Paciente
    template_name = "pacientes/paciente_confirm_delete.html"
    success_url = reverse_lazy("paciente_list")

    def post(self, request, *args, **kwargs):
        # Override POST to add success message after deletion
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Paciente excluído com sucesso.")
        return response
