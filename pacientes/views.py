from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Paciente
from .forms import PacienteForm


class PacienteListView(ListView):
    model = Paciente
    template_name = "pacientes/paciente_list.html"
    context_object_name = "pacientes"
    ordering = ["nome"]  # Ordena por nome


class PacienteCreateView(CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")


class PacienteUpdateView(UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")


class PacienteDeleteView(DeleteView):
    model = Paciente
    template_name = "pacientes/paciente_confirm_delete.html"
    success_url = reverse_lazy("paciente_list")
