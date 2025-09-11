from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
import datetime

from .models import Viagem
from viagens.forms import ViagemForm


# Listar todas as viagens
class ViagemListView(ListView):
    model = Viagem
    template_name = 'viagens/viagem_list.html'
    context_object_name = 'viagens'

    def get_queryset(self):
        qs = super().get_queryset()
        # parâmetros: ?data=YYYY-MM-DD ou ?start=YYYY-MM-DD&end=YYYY-MM-DD
        data = self.request.GET.get('data')
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')

        # nome do campo de data no model
        field = 'data_viagem'

        # se o usuário informou parâmetros, usa-os
        if data or start or end:
            if data:
                d = parse_date(data)
                if d:
                    return qs.filter(**{field: d})

            if start or end:
                s = parse_date(start) if start else None
                e = parse_date(end) if end else None
                if s and e:
                    return qs.filter(**{f"{field}__range": (s, e)})
                if s:
                    return qs.filter(**{f"{field}__gte": s})
                if e:
                    return qs.filter(**{f"{field}__lte": e})

        # comportamento padrão: mostrar viagens da data atual
        hoje = datetime.date.today()
        return qs.filter(**{field: hoje})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # preencher inputs com valores da querystring; padrão = hoje
        hoje_str = datetime.date.today().isoformat()
        ctx['filter_data'] = self.request.GET.get('data', hoje_str)
        ctx['filter_start'] = self.request.GET.get('start', '')
        ctx['filter_end'] = self.request.GET.get('end', '')
        return ctx


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
