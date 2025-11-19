from django.contrib.auth.mixins import LoginRequiredMixin
from secretaria_it.access import AccessRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.dateparse import parse_date
import datetime
from .models import Viagem, TipoAtendimentoViagem, HospitalAtendimento, DestinoViagem
from pacientes.models import Paciente
from .forms import ViagemForm, TipoAtendimentoViagemForm, HospitalAtendimentoForm, DestinoViagemForm

class ViagemListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'viagens'
    model = Viagem
    template_name = 'viagens/viagem_list.html'
    context_object_name = 'viagens'

    def get_queryset(self):
        qs = super().get_queryset()
        paciente_id = self.request.GET.get('paciente')
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
        destino_filtro = (self.request.GET.get('destino') or '').strip()
        if destino_filtro:
            qs = qs.filter(destino__iexact=destino_filtro)
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        field = 'data_viagem'

        # Definir data inicial padrão como hoje quando não informada
        hoje = datetime.date.today()
        start_date = parse_date(start) if start else hoje
        end_date = parse_date(end) if end else None

        if start_date and end_date:
            qs = qs.filter(**{f"{field}__range": (start_date, end_date)})
        elif start_date:
            qs = qs.filter(**{f"{field}__gte": start_date})
        elif end_date:
            qs = qs.filter(**{f"{field}__lte": end_date})

        # Se nenhuma data for informada, garantir filtro do dia atual
        if not start and not end:
            qs = qs.filter(**{field: hoje})

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoje_str = datetime.date.today().isoformat()
        ctx['filter_start'] = self.request.GET.get('start', hoje_str)
        ctx['filter_end'] = self.request.GET.get('end', '')
        ctx['filter_destino'] = (self.request.GET.get('destino') or '').strip()
        ctx['today'] = datetime.date.today()
        ctx.setdefault('tipo_atendimento_form', TipoAtendimentoViagemForm(initial={'ativo': True}))
        ctx.setdefault('hospital_atendimento_form', HospitalAtendimentoForm(initial={'ativo': True}))
        ctx.setdefault('destino_form', DestinoViagemForm(initial={'ativo': True}))
        ctx['tipos_atendimento'] = TipoAtendimentoViagem.objects.order_by('nome')
        ctx['hospitais_atendimento'] = HospitalAtendimento.objects.order_by('nome')
        ctx['destinos_viagem'] = DestinoViagem.objects.order_by('nome_cidade', 'uf')
        destinos_cadastrados = {
            f"{d.nome_cidade}/{d.uf}" for d in DestinoViagem.objects.filter(ativo=True)
        }
        destinos_registrados = set(
            Viagem.objects.order_by().values_list('destino', flat=True).distinct()
        )
        ctx['destinos_disponiveis'] = sorted(
            {d for d in (destinos_cadastrados | destinos_registrados) if (d or '').strip()}
        )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        action = request.POST.get('_action')

        if action == 'tipo-atendimento':
            form = TipoAtendimentoViagemForm(request.POST)
            if form.is_valid():
                obj = form.save()
                messages.success(request, f"Tipo de atendimento '{obj.nome}' cadastrado com sucesso.")
                return redirect('viagem-list')
            context = self.get_context_data(tipo_atendimento_form=form)
            return self.render_to_response(context)

        if action == 'hospital-atendimento':
            form = HospitalAtendimentoForm(request.POST)
            if form.is_valid():
                obj = form.save()
                messages.success(request, f"Hospital de atendimento '{obj.nome}' cadastrado com sucesso.")
                return redirect('viagem-list')
            context = self.get_context_data(hospital_atendimento_form=form)
            return self.render_to_response(context)

        if action == 'destino':
            form = DestinoViagemForm(request.POST)
            if form.is_valid():
                obj = form.save()
                messages.success(request, f"Cidade de destino '{obj}' cadastrada com sucesso.")
                return redirect('viagem-list')
            context = self.get_context_data(destino_form=form)
            return self.render_to_response(context)

        messages.error(request, 'Ação inválida para cadastro de viagens.')
        return redirect('viagem-list')

class ViagemCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'viagens'
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')

    def get_initial(self):
        initial = super().get_initial()
        try:
            pid = int(self.request.GET.get('paciente') or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid:
            initial['paciente'] = pid
            if not initial.get('endereco_paciente'):
                paciente = Paciente.objects.filter(pk=pid).first()
                if paciente:
                    partes = []
                    if getattr(paciente, 'logradouro', None):
                        partes.append(paciente.logradouro)
                    if getattr(paciente, 'numero', None):
                        partes.append(f"nº {paciente.numero}")
                    if getattr(paciente, 'bairro', None):
                        partes.append(paciente.bairro)
                    if getattr(paciente, 'cep', None):
                        partes.append(f"CEP: {paciente.cep}")
                    if partes:
                        initial['endereco_paciente'] = ", ".join(partes)
        return initial

    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Viagem criada com sucesso.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao criar viagem. Verifique os dados e tente novamente.')
        return super().form_invalid(form)

class ViagemUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'viagens'
    model = Viagem
    form_class = ViagemForm
    template_name = 'viagens/viagem_form.html'
    success_url = reverse_lazy('viagem-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Viagem atualizada com sucesso.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar viagem. Verifique os dados e tente novamente.')
        return super().form_invalid(form)


class ViagemDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'viagens'
    model = Viagem
    template_name = 'viagens/viagem_confirm_delete.html'
    success_url = reverse_lazy('viagem-list')

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'Viagem excluída com sucesso.')
        return response
