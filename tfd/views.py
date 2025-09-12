from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy

from .models import TFD
from .forms import TFDForm


from datetime import date
from django.utils.dateparse import parse_date
from django.db.models import Q


class TFDListView(ListView):
    model = TFD
    template_name = 'tfd/tfd_list.html'
    context_object_name = 'tfds'

    def get_queryset(self):
        qs = super().get_queryset()

        # leitura dos parâmetros GET
        start_raw = self.request.GET.get('start_date')
        end_raw = self.request.GET.get('end_date')

        # parse com fallback para hoje
        start = parse_date(start_raw) if start_raw else date.today()
        end = parse_date(end_raw) if end_raw else date.today()

        # garantir ordem correta
        if start and end and start > end:
            start, end = end, start

        # Filtrar registros cujo período (data_inicio..data_fim) se sobrepõe ao intervalo [start, end].
        # Condição de sobreposição: NOT (data_fim < start OR data_inicio > end)
        qs = qs.filter(
            Q(data_fim__isnull=True) |
            (~Q(data_fim__lt=start) & ~Q(data_inicio__gt=end))
        )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # repassa os valores para preencher o formulário de filtro na template
        ctx['filter_start'] = self.request.GET.get('start_date') or date.today().isoformat()
        ctx['filter_end'] = self.request.GET.get('end_date') or date.today().isoformat()
        return ctx


class TFDCreateView(CreateView):
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')


class TFDUpdateView(UpdateView):
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')


class TFDDetailView(DetailView):
    model = TFD
    template_name = 'tfd/tfd_detail.html'
    context_object_name = 'tfd'


class TFDPrintView(DetailView):
    model = TFD
    template_name = 'tfd/tfd_print.html'
    context_object_name = 'tfd'

# Create your views here.
