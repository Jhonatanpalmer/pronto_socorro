from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.db.models import Q
from django.db.models.functions import Coalesce
from .models import TFD
from .forms import TFDForm

# Lista de TFDs
class TFDListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = TFD
    template_name = 'tfd/tfd_list.html'
    context_object_name = 'tfds'
    
    def get_queryset(self):
        qs = super().get_queryset()
        start = self.request.GET.get('start_date')
        end = self.request.GET.get('end_date')

        s = parse_date(start) if start else None
        e = parse_date(end) if end else None

        # If both start and end provided, return TFDs whose period overlaps [s, e].
        # Treat data_fim NULL as equal to data_inicio using Coalesce.
        if s and e:
            qs = qs.annotate(record_end=Coalesce('data_fim', 'data_inicio'))
            qs = qs.filter(Q(data_inicio__lte=e) & Q(record_end__gte=s))
        elif s:
            # show records that end on/after s (overlap with [s, +inf))
            qs = qs.annotate(record_end=Coalesce('data_fim', 'data_inicio'))
            qs = qs.filter(record_end__gte=s)
        elif e:
            # show records that start on/before e (overlap with (-inf, e])
            qs = qs.filter(data_inicio__lte=e)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_start'] = self.request.GET.get('start_date', '')
        ctx['filter_end'] = self.request.GET.get('end_date', '')
        return ctx

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