from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
import datetime
from .models import Viagem
from .forms import ViagemForm

class ViagemListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = Viagem
    template_name = 'viagens/viagem_list.html'
    context_object_name = 'viagens'

    def get_queryset(self):
        qs = super().get_queryset()
        data = self.request.GET.get('data')
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        cidade = self.request.GET.get('cidade')
        field = 'data_viagem'

        if cidade:
            qs = qs.filter(destino__icontains=cidade)

        if data:
            d = parse_date(data)
            if d:
                qs = qs.filter(**{field: d})

        if start or end:
            s = parse_date(start) if start else None
            e = parse_date(end) if end else None
            if s and e:
                qs = qs.filter(**{f"{field}__range": (s, e)})
            elif s:
                qs = qs.filter(**{f"{field}__gte": s})
            elif e:
                qs = qs.filter(**{f"{field}__lte": e})

        if not data and not start and not end:
            hoje = datetime.date.today()
            qs = qs.filter(**{field: hoje})

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje_str = datetime.date.today().isoformat()
        ctx['filter_data'] = self.request.GET.get('data', hoje_str)
        ctx['filter_start'] = self.request.GET.get('start', '')
        ctx['filter_end'] = self.request.GET.get('end', '')
        ctx['filter_cidade'] = self.request.GET.get('cidade', '')
        ctx['cidades'] = Viagem.objects.values_list("destino", flat=True).distinct()
        ctx['today'] = datetime.date.today()
        return ctx

class ViagemCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')

class ViagemUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')
