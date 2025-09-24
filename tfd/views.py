from django.contrib.auth.mixins import LoginRequiredMixin
from secretaria_it.access import AccessRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import TFD
from .forms import TFDForm

# Lista de TFDs
class TFDListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'tfd'
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
        
        # Calcular valor total dos TFDs filtrados
        queryset = self.get_queryset()
        valor_total_geral = queryset.aggregate(total=Sum('valor_total'))['total'] or 0
        ctx['valor_total_geral'] = valor_total_geral
        
        # Informações sobre o filtro para exibição
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        
        if start_date or end_date:
            if start_date and end_date:
                ctx['periodo_filtro'] = f"Período: {parse_date(start_date).strftime('%d/%m/%Y')} a {parse_date(end_date).strftime('%d/%m/%Y')}"
            elif start_date:
                ctx['periodo_filtro'] = f"A partir de: {parse_date(start_date).strftime('%d/%m/%Y')}"
            elif end_date:
                ctx['periodo_filtro'] = f"Até: {parse_date(end_date).strftime('%d/%m/%Y')}"
        else:
            ctx['periodo_filtro'] = "Todos os registros"
            
        # Adicionar data atual para relatórios
        ctx['today'] = timezone.now()
            
        return ctx

# Detalhe de um TFD
class TFDDetailView(AccessRequiredMixin, LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    access_key = 'tfd'
    model = TFD
    template_name = 'tfd/tfd_detail.html'
    context_object_name = 'tfd'

# Criar TFD
class TFDCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'tfd'
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')

# Editar TFD
class TFDUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'tfd'
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')

# Deletar TFD
class TFDDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'tfd'
    model = TFD
    template_name = 'tfd/tfd_confirm_delete.html'
    success_url = reverse_lazy('tfd-list')

class TFDPrintView(DetailView):
    model = TFD
    template_name = 'tfd/tfd_print.html'  # Você precisa criar esse template
    context_object_name = 'tfd'