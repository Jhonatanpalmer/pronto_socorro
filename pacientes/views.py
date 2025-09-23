from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente
from .forms import PacienteForm

class PacienteListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = Paciente
    template_name = "pacientes/paciente_list.html"
    context_object_name = "pacientes"
    ordering = ["nome"]
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q)
                | Q(cpf__icontains=q)
                | Q(cns__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        return ctx


@login_required
def paciente_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    limit = int(request.GET.get("limit") or 20)
    limit = max(1, min(limit, 50))
    qs = Paciente.objects.all()
    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(cns__icontains=q)
        )
    qs = qs.order_by("nome").values("id", "nome", "cpf", "cns", "endereco", "telefone")[:limit]
    results = []
    for r in qs:
        label_parts = [r.get("nome") or ""]
        if r.get("cpf"):
            label_parts.append(f"CPF: {r['cpf']}")
        if r.get("cns"):
            label_parts.append(f"CNS: {r['cns']}")
        results.append({
            "id": r["id"],
            "nome": r["nome"],
            "cpf": r.get("cpf"),
            "cns": r.get("cns"),
            "endereco": r.get("endereco") or "",
            "telefone": r.get("telefone") or "",
            "label": " | ".join(p for p in label_parts if p),
        })
    return JsonResponse({"results": results})

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
