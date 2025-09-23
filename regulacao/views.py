from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.forms import modelformset_factory
from django.db import transaction
from django.core.paginator import Paginator
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame, Especialidade, RegulacaoConsulta
from pacientes.models import Paciente
import base64
from io import BytesIO
from .forms import (
    UBSForm, MedicoSolicitanteForm, TipoExameForm, RegulacaoExameForm,
    RegulacaoExameCreateForm, EspecialidadeForm, RegulacaoConsultaForm,
    RegulacaoExameBatchForm, RegulacaoConsultaBatchForm, SIGTAPImportForm
)
import os
import shutil
import tempfile


# ============ VIEWS PARA UBS ============

class UBSListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = UBS
    template_name = 'regulacao/ubs_list.html'
    context_object_name = 'ubs_list'
    ordering = ['nome']


class UBSCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = UBS
    form_class = UBSForm
    template_name = 'regulacao/ubs_form.html'
    success_url = reverse_lazy('ubs-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'UBS cadastrada com sucesso!')
        return super().form_valid(form)


class UBSUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = UBS
    form_class = UBSForm
    template_name = 'regulacao/ubs_form.html'
    success_url = reverse_lazy('ubs-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'UBS atualizada com sucesso!')
        return super().form_valid(form)


class UBSDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = UBS
    template_name = 'regulacao/ubs_confirm_delete.html'
    success_url = reverse_lazy('ubs-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'UBS excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA MÉDICOS ============

class MedicoListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = MedicoSolicitante
    template_name = 'regulacao/medicosolicitante_list.html'
    context_object_name = 'medico_list'
    ordering = ['nome']


class MedicoCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = MedicoSolicitante
    form_class = MedicoSolicitanteForm
    template_name = 'regulacao/medicosolicitante_form.html'
    success_url = reverse_lazy('medico-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Médico cadastrado com sucesso!')
        return super().form_valid(form)


class MedicoUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = MedicoSolicitante
    form_class = MedicoSolicitanteForm
    template_name = 'regulacao/medicosolicitante_form.html'
    success_url = reverse_lazy('medico-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Médico atualizado com sucesso!')
        return super().form_valid(form)


class MedicoDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = MedicoSolicitante
    template_name = 'regulacao/medicosolicitante_confirm_delete.html'
    success_url = reverse_lazy('medico-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Médico excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA TIPOS DE EXAMES ============

class TipoExameListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = TipoExame
    template_name = 'regulacao/tipoexame_list.html'
    context_object_name = 'tipoexame_list'
    ordering = ['nome']


class TipoExameCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'regulacao/tipoexame_form.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de exame cadastrado com sucesso!')
        return super().form_valid(form)


class TipoExameUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'regulacao/tipoexame_form.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de exame atualizado com sucesso!')
        return super().form_valid(form)


class TipoExameDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = TipoExame
    template_name = 'regulacao/tipoexame_confirm_delete.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de exame excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA REGULAÇÃO DE EXAMES ============

class RegulacaoListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = RegulacaoExame
    template_name = 'regulacao/regulacaoexame_list.html'
    context_object_name = 'regulacaoexame_list'
    paginate_by = 20
    
    def get_queryset(self):
        qs = RegulacaoExame.objects.select_related('paciente', 'ubs_solicitante', 'medico_solicitante', 'tipo_exame')
        
        # Aplicar filtros
        status = self.request.GET.get('status')
        ubs = self.request.GET.get('ubs')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        
        if status:
            qs = qs.filter(status=status)
        if ubs:
            qs = qs.filter(ubs_solicitante_id=ubs)
        if data_inicio:
            qs = qs.filter(data_solicitacao__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_solicitacao__date__lte=data_fim)
            
        return qs.order_by('-data_solicitacao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ubs_list'] = UBS.objects.filter(ativa=True).order_by('nome')

        # Agrupar SEMPRE por paciente, respeitando filtros aplicados no queryset base
        base_qs = self.get_queryset()
        grupos = {}
        for reg in base_qs:
            pid = reg.paciente_id
            if pid not in grupos:
                grupos[pid] = {
                    'paciente': reg.paciente,
                    'paciente_id': pid,
                    'total_exames': 0,
                    'exames_nomes': [],
                    'primeira_hora': reg.data_solicitacao,
                }
            g = grupos[pid]
            g['total_exames'] += 1
            if reg.tipo_exame and reg.tipo_exame.nome not in g['exames_nomes']:
                g['exames_nomes'].append(reg.tipo_exame.nome)
            if reg.data_solicitacao and reg.data_solicitacao < g['primeira_hora']:
                g['primeira_hora'] = reg.data_solicitacao

        pacientes_grouped = sorted(grupos.values(), key=lambda x: (x['paciente'].nome or '').lower())

        # Paginar os pacientes agrupados usando o mesmo parâmetro de página
        page = self.request.GET.get('page') or 1
        paginator = Paginator(pacientes_grouped, self.paginate_by or 20)
        pacientes_page = paginator.get_page(page)

        context['pacientes_page'] = pacientes_page
        context['paginator'] = paginator
        context['mostrando_agrupado'] = True
        return context


class RegulacaoCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = RegulacaoExame
    form_class = RegulacaoExameCreateForm
    template_name = 'regulacao/regulacaoexame_form.html'
    success_url = reverse_lazy('regulacao-list')
    
    def form_valid(self, form):
        # Cria múltiplas solicitações, uma por tipo de exame selecionado, compartilhando o mesmo numero_pedido
        cleaned = form.cleaned_data
        tipos = cleaned.get('tipos_exame')
        if not tipos:
            messages.error(self.request, 'Selecione ao menos um tipo de exame.')
            return self.form_invalid(form)

        # Gerar um número de pedido agrupador
        from datetime import datetime
        numero_pedido = f"PED{datetime.now().strftime('%Y%m%d%H%M%S')}"

        created = []
        with transaction.atomic():
            for tipo in tipos:
                obj = RegulacaoExame(
                    paciente=cleaned['paciente'],
                    ubs_solicitante=cleaned['ubs_solicitante'],
                    medico_solicitante=cleaned['medico_solicitante'],
                    tipo_exame=tipo,
                    justificativa=cleaned['justificativa'],
                    prioridade=cleaned['prioridade'],
                    observacoes_solicitacao=cleaned.get('observacoes_solicitacao', ''),
                    status='fila',
                    numero_pedido=numero_pedido,
                )
                obj.save()
                created.append(obj)

        messages.success(self.request, f"Solicitação criada com {len(created)} exame(s) no pedido {numero_pedido}.")
        # Redireciona para a lista; poderíamos direcionar para o detalhe do primeiro
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        print(f"DEBUG RegulacaoCreateView: Formulário inválido! Erros: {form.errors}")
        messages.error(self.request, 'Por favor, corrija os erros no formulário.')
        return super().form_invalid(form)


class RegulacaoDetailView(LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    model = RegulacaoExame
    template_name = 'regulacao/regulacao_detail.html'
    context_object_name = 'regulacao'


class RegulacaoUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = RegulacaoExame
    form_class = RegulacaoExameForm
    template_name = 'regulacao/regulacaoexame_form.html'
    success_url = reverse_lazy('regulacao-list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Solicitação atualizada com sucesso! Protocolo: {form.instance.numero_protocolo}')
        return super().form_valid(form)


class RegulacaoDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = RegulacaoExame
    template_name = 'regulacao/regulacaoexame_confirm_delete.html'
    success_url = reverse_lazy('regulacao-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Solicitação de regulação excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# View regular_exame removida: autorização/agendamento passou a ser feito via tela por paciente (paciente_pedido)


@login_required
def regular_consulta(request, pk):
    """Redireciona para a tela unificada de autorização por paciente."""
    regulacao = get_object_or_404(RegulacaoConsulta, pk=pk)
    # Mensagem opcional para indicar o novo fluxo
    messages.info(request, 'Fluxo atualizado: autorização é feita na página do paciente.')
    return redirect('paciente-pedido', paciente_id=regulacao.paciente_id)


@login_required
def dashboard_regulacao(request):
    """Dashboard com estatísticas da regulação"""
    # Filtros rápidos de período para listas recentes
    period_ex = (request.GET.get('period_ex') or '7').lower()
    period_co = (request.GET.get('period_co') or '7').lower()
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.localdate()

    def get_cutoff(period: str):
        if period in ('todos', 'all', 'tudo'):
            return None
        if period in ('hoje', 'today'):
            return today
        try:
            days = int(period)
            if days <= 1:
                return today
            return today - timedelta(days=days-1)
        except Exception:
            return today - timedelta(days=6)  # padrão 7 dias

    cutoff_ex = get_cutoff(period_ex)
    cutoff_co = get_cutoff(period_co)

    # Métricas para consultas autorizadas
    total_consultas_autorizadas = RegulacaoConsulta.objects.filter(status='autorizado').count()
    consultas_autorizadas_qs = RegulacaoConsulta.objects.select_related(
        'paciente', 'ubs_solicitante', 'especialidade'
    ).filter(status='autorizado')
    if cutoff_co:
        consultas_autorizadas_qs = consultas_autorizadas_qs.filter(data_regulacao__date__gte=cutoff_co)
    consultas_autorizadas_recentes = consultas_autorizadas_qs.order_by('-data_regulacao', '-data_solicitacao')[:10]

    # Quantidade de pacientes distintos na fila (exames e consultas)
    exames_fila_pacientes = RegulacaoExame.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
    consultas_fila_pacientes = RegulacaoConsulta.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
    pacientes_fila_exames_count = exames_fila_pacientes.count()
    pacientes_fila_consultas_count = consultas_fila_pacientes.count()
    pacientes_fila_count = len(set(list(exames_fila_pacientes) + list(consultas_fila_pacientes)))

    context = {
        'total_pendentes': RegulacaoExame.objects.filter(status='pendente').count(),
        'total_autorizados': RegulacaoExame.objects.filter(status='autorizado').count(),
        'total_negados': RegulacaoExame.objects.filter(status='negado').count(),
        'total_ubs': UBS.objects.filter(ativa=True).count(),
        'total_medicos': MedicoSolicitante.objects.filter(ativo=True).count(),
        'total_tipos_exame': TipoExame.objects.filter(ativo=True).count(),
        'total_consultas_fila': RegulacaoConsulta.objects.filter(status='fila').count(),
        'regulacoes_recentes': (lambda: (
            RegulacaoExame.objects.select_related('paciente', 'ubs_solicitante', 'tipo_exame')
            .filter(status='autorizado')
            .filter(**({'data_regulacao__date__gte': cutoff_ex} if cutoff_ex else {}))
            .order_by('-data_regulacao', '-data_solicitacao')[:10]
        ))(),
        'total_consultas_autorizadas': total_consultas_autorizadas,
        'consultas_autorizadas_recentes': consultas_autorizadas_recentes,
    'pacientes_fila_count': pacientes_fila_count,
    'pacientes_fila_exames_count': pacientes_fila_exames_count,
    'pacientes_fila_consultas_count': pacientes_fila_consultas_count,
        'period_ex': period_ex,
        'period_co': period_co,
    }
    return render(request, 'regulacao/dashboard.html', context)


# ============ CONSULTAS (Especialidades) ============

class EspecialidadeListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = Especialidade
    template_name = 'regulacao/especialidade_list.html'
    context_object_name = 'especialidades'
    ordering = ['nome']


class EspecialidadeCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'regulacao/especialidade_form.html'
    success_url = reverse_lazy('especialidade-list')


class EspecialidadeUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = Especialidade
    form_class = EspecialidadeForm
    template_name = 'regulacao/especialidade_form.html'
    success_url = reverse_lazy('especialidade-list')


class EspecialidadeDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = Especialidade
    template_name = 'regulacao/especialidade_confirm_delete.html'
    success_url = reverse_lazy('especialidade-list')


class RegulacaoConsultaListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    template_name = 'regulacao/regulacaoconsulta_list.html'
    context_object_name = 'solicitacoes'
    paginate_by = 20

    def get_queryset(self):
        qs = RegulacaoConsulta.objects.select_related('paciente', 'ubs_solicitante', 'medico_solicitante', 'especialidade')
        status = self.request.GET.get('status')
        ubs = self.request.GET.get('ubs')
        if status:
            qs = qs.filter(status=status)
        if ubs:
            qs = qs.filter(ubs_solicitante_id=ubs)
        return qs.order_by('-data_solicitacao')


class RegulacaoConsultaCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    form_class = RegulacaoConsultaForm
    template_name = 'regulacao/regulacaoconsulta_form.html'
    success_url = reverse_lazy('consulta-list')


class RegulacaoConsultaUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    form_class = RegulacaoConsultaForm
    template_name = 'regulacao/regulacaoconsulta_form.html'
    success_url = reverse_lazy('consulta-list')

    def form_valid(self, form):
        messages.success(self.request, 'Solicitação de consulta atualizada com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Não foi possível salvar. Verifique os campos e tente novamente.')
        return super().form_invalid(form)


class RegulacaoConsultaDetailView(LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    template_name = 'regulacao/regulacaoconsulta_detail.html'
    context_object_name = 'regulacao'


class RegulacaoConsultaDeleteView(LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    template_name = 'regulacao/regulacaoconsulta_confirm_delete.html'
    success_url = reverse_lazy('consulta-list')


@login_required
def fila_espera(request):
    """Fila de espera unificada para exames e consultas (status = fila)."""
    from django.db.models import Q
    q_ex = (request.GET.get('q_ex') or '').strip()
    q_co = (request.GET.get('q_co') or '').strip()
    only = (request.GET.get('only') or '').strip()

    exames_qs = RegulacaoExame.objects.select_related('paciente', 'tipo_exame', 'ubs_solicitante').filter(status='fila')
    if q_ex:
        exames_qs = exames_qs.filter(
            Q(paciente__nome__icontains=q_ex) |
            Q(paciente__cpf__icontains=q_ex) |
            Q(paciente__cns__icontains=q_ex) |
            Q(tipo_exame__nome__icontains=q_ex) |
            Q(ubs_solicitante__nome__icontains=q_ex)
        )
    exames_qs = exames_qs.order_by('paciente__nome', 'data_solicitacao')

    consultas_qs = RegulacaoConsulta.objects.select_related('paciente', 'especialidade', 'ubs_solicitante').filter(status='fila')
    if q_co:
        consultas_qs = consultas_qs.filter(
            Q(paciente__nome__icontains=q_co) |
            Q(paciente__cpf__icontains=q_co) |
            Q(paciente__cns__icontains=q_co) |
            Q(especialidade__nome__icontains=q_co) |
            Q(ubs_solicitante__nome__icontains=q_co)
        )
    consultas_qs = consultas_qs.order_by('paciente__nome', 'data_solicitacao')

    # Agrupar por paciente - Exames
    grupos_ex = {}
    for r in exames_qs:
        pid = r.paciente_id
        if pid not in grupos_ex:
            grupos_ex[pid] = {
                'paciente': r.paciente,
                'paciente_id': pid,
                'total': 0,
                'nomes': [],  # nomes de exames únicos
                'desde': r.data_solicitacao,
            }
        g = grupos_ex[pid]
        g['total'] += 1
        nome = r.tipo_exame.nome if r.tipo_exame else ''
        if nome and nome not in g['nomes']:
            g['nomes'].append(nome)
        if r.data_solicitacao < g['desde']:
            g['desde'] = r.data_solicitacao

    exames_grouped = sorted(grupos_ex.values(), key=lambda x: (x['paciente'].nome or '').lower())

    # Agrupar por paciente - Consultas
    grupos_co = {}
    for r in consultas_qs:
        pid = r.paciente_id
        if pid not in grupos_co:
            grupos_co[pid] = {
                'paciente': r.paciente,
                'paciente_id': pid,
                'total': 0,
                'nomes': [],  # nomes de especialidades únicos
                'desde': r.data_solicitacao,
            }
        g = grupos_co[pid]
        g['total'] += 1
        nome = r.especialidade.nome if r.especialidade else ''
        if nome and nome not in g['nomes']:
            g['nomes'].append(nome)
        if r.data_solicitacao < g['desde']:
            g['desde'] = r.data_solicitacao

    consultas_grouped = sorted(grupos_co.values(), key=lambda x: (x['paciente'].nome or '').lower())

    # Paginação independente
    try:
        per_page_ex = int(request.GET.get('per_ex', 25))
    except (TypeError, ValueError):
        per_page_ex = 25
    try:
        per_page_co = int(request.GET.get('per_co', 25))
    except (TypeError, ValueError):
        per_page_co = 25

    page_ex = request.GET.get('page_ex') or 1
    page_co = request.GET.get('page_co') or 1

    p_ex = Paginator(exames_grouped, per_page_ex)
    p_co = Paginator(consultas_grouped, per_page_co)
    exames_page = p_ex.get_page(page_ex)
    consultas_page = p_co.get_page(page_co)

    return render(request, 'regulacao/fila_espera.html', {
        'exames': exames_page,
        'consultas': consultas_page,
        'q_ex': q_ex,
        'q_co': q_co,
        'p_ex': p_ex,
        'p_co': p_co,
        'per_ex': per_page_ex,
        'per_co': per_page_co,
        'only': only,
    })


@login_required
def agenda_regulacao(request):
    """Agenda da regulação: itens autorizados com data/hora agendadas."""
    exames = RegulacaoExame.objects.select_related('paciente', 'tipo_exame', 'ubs_solicitante').filter(status='autorizado', data_agendada__isnull=False).order_by('data_agendada', 'hora_agendada')
    consultas = RegulacaoConsulta.objects.select_related('paciente', 'especialidade', 'ubs_solicitante').filter(status='autorizado', data_agendada__isnull=False).order_by('data_agendada', 'hora_agendada')
    return render(request, 'regulacao/agenda.html', {
        'exames': exames,
        'consultas': consultas,
    })


@login_required
def status_ubs(request, ubs_id):
    """Tela para a UBS ver o status das suas solicitações."""
    ubs = get_object_or_404(UBS, pk=ubs_id)
    exames = RegulacaoExame.objects.filter(ubs_solicitante=ubs).select_related('paciente', 'tipo_exame').order_by('-data_solicitacao')
    consultas = RegulacaoConsulta.objects.filter(ubs_solicitante=ubs).select_related('paciente', 'especialidade').order_by('-data_solicitacao')
    return render(request, 'regulacao/status_ubs.html', {
        'ubs': ubs,
        'exames': exames,
        'consultas': consultas,
    })

#### Precisco ajusar o qrcode 
def _qrcode_base64(texto: str):
    try:
        import importlib
        qrcode = importlib.import_module('qrcode')
        img = qrcode.make(texto)
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return None

@login_required
def comprovante_exame(request, pk: int):
    reg = get_object_or_404(RegulacaoExame.objects.select_related('paciente','tipo_exame','ubs_solicitante','medico_atendente'), pk=pk)
    qr = _qrcode_base64(reg.numero_protocolo)
    return render(request, 'regulacao/comprovante_exame.html', {
        'reg': reg,
        'qr_base64': qr,
    })

@login_required
def comprovante_consulta(request, pk: int):
    reg = get_object_or_404(RegulacaoConsulta.objects.select_related('paciente','especialidade','ubs_solicitante','medico_atendente'), pk=pk)
    qr = _qrcode_base64(reg.numero_protocolo)
    return render(request, 'regulacao/comprovante_consulta.html', {
        'reg': reg,
        'qr_base64': qr,
    })

@login_required
def paciente_pedido(request, paciente_id):
    """Página única por paciente para listar todas as solicitações e autorizar/agendar seleções."""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    # Exames do paciente (todos para contexto; foco em fila/pendente para autorizar)
    exames_qs = RegulacaoExame.objects.select_related('tipo_exame', 'ubs_solicitante', 'medico_solicitante').filter(paciente=paciente).order_by('-data_solicitacao')
    exames_pendentes_qs = exames_qs.filter(status__in=['fila', 'pendente'])

    # Consultas do paciente
    consultas_qs = RegulacaoConsulta.objects.select_related('especialidade', 'ubs_solicitante', 'medico_solicitante').filter(paciente=paciente).order_by('-data_solicitacao')
    consultas_pendentes_qs = consultas_qs.filter(status__in=['fila', 'pendente'])

    ExameFormSet = modelformset_factory(RegulacaoExame, form=RegulacaoExameBatchForm, extra=0, can_delete=False)
    ConsultaFormSet = modelformset_factory(RegulacaoConsulta, form=RegulacaoConsultaBatchForm, extra=0, can_delete=False)

    if request.method == 'POST':
        submitted_exames = 'submit_exames' in request.POST
        submitted_consultas = 'submit_consultas' in request.POST
        exame_fs = ExameFormSet(request.POST if submitted_exames else None, queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(request.POST if submitted_consultas else None, queryset=consultas_pendentes_qs, prefix='co')
        # ajustar queryset de médicos
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            if 'medico_atendente' in f.fields:
                f.fields['medico_atendente'].queryset = MedicoSolicitante.objects.filter(ativo=True).order_by('nome')

        # Processar apenas o formset submetido
        from django.utils import timezone
        if submitted_exames:
            if exame_fs.is_valid():
                aprovados_exames = 0
                with transaction.atomic():
                    for form in exame_fs.forms:
                        inst = form.instance
                        if form.cleaned_data.get('autorizar'):
                            inst.status = 'autorizado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            inst.local_realizacao = form.cleaned_data.get('local_realizacao')
                            inst.data_agendada = form.cleaned_data.get('data_agendada')
                            inst.hora_agendada = form.cleaned_data.get('hora_agendada')
                            inst.medico_atendente = form.cleaned_data.get('medico_atendente')
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.save()
                            aprovados_exames += 1
                if aprovados_exames:
                    messages.success(request, f"{aprovados_exames} exame(s) autorizados e agendados para {paciente.nome}.")
                else:
                    messages.info(request, 'Nenhum exame marcado para autorização.')
                return redirect('paciente-pedido', paciente_id=paciente.id)
            else:
                messages.error(request, 'Corrija os erros nos exames para prosseguir.')

        if submitted_consultas:
            if consulta_fs.is_valid():
                aprovados_consultas = 0
                with transaction.atomic():
                    for form in consulta_fs.forms:
                        inst = form.instance
                        if form.cleaned_data.get('autorizar'):
                            inst.status = 'autorizado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            inst.local_atendimento = form.cleaned_data.get('local_atendimento')
                            inst.data_agendada = form.cleaned_data.get('data_agendada')
                            inst.hora_agendada = form.cleaned_data.get('hora_agendada')
                            inst.medico_atendente = form.cleaned_data.get('medico_atendente')
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.save()
                            aprovados_consultas += 1
                if aprovados_consultas:
                    messages.success(request, f"{aprovados_consultas} consulta(s) autorizadas e agendadas para {paciente.nome}.")
                else:
                    messages.info(request, 'Nenhuma consulta marcada para autorização.')
                return redirect('paciente-pedido', paciente_id=paciente.id)
            else:
                messages.error(request, 'Corrija os erros nas consultas para prosseguir.')
    else:
        exame_fs = ExameFormSet(queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(queryset=consultas_pendentes_qs, prefix='co')
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            if 'medico_atendente' in f.fields:
                f.fields['medico_atendente'].queryset = MedicoSolicitante.objects.filter(ativo=True).order_by('nome')

    return render(request, 'regulacao/paciente_pedido.html', {
        'paciente': paciente,
        'exame_formset': exame_fs,
        'consulta_formset': consulta_fs,
        'exames_todos': exames_qs,
        'exames_pendentes_count': exames_pendentes_qs.count(),
        'consultas_todas': consultas_qs,
        'consultas_pendentes_count': consultas_pendentes_qs.count(),
    })


@login_required
def importar_sigtap(request):
    """Upload do pacote SIGTAP (.rar/.zip), extração no servidor e importação em TipoExame."""
    form = SIGTAPImportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        up = form.cleaned_data['arquivo']
        only_groups = form.cleaned_data.get('only_groups') or ''
        name_contains = form.cleaned_data.get('name_contains') or ''
        set_valor = bool(form.cleaned_data.get('set_valor'))
        encoding = (form.cleaned_data.get('encoding') or 'latin-1').strip() or 'latin-1'

        # Criar pasta temporária
        temp_dir = tempfile.mkdtemp(prefix='sigtap_')
        archive_path = os.path.join(temp_dir, up.name)
        try:
            # Salvar upload
            with open(archive_path, 'wb') as dest:
                for chunk in up.chunks():
                    dest.write(chunk)

            # Extrair
            extract_dir = os.path.join(temp_dir, 'extract')
            os.makedirs(extract_dir, exist_ok=True)

            lowered = up.name.lower()
            if lowered.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(extract_dir)
            elif lowered.endswith('.rar'):
                # Usar utilitário externo (7-Zip). Tentar 7z e 7za.
                import subprocess
                extracted = False
                for bin_name in ('7z', '7za'):
                    try:
                        subprocess.check_call([bin_name, 'x', '-y', f'-o{extract_dir}', archive_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        extracted = True
                        break
                    except Exception:
                        continue
                if not extracted:
                    messages.error(request, 'Não foi possível extrair o .rar. Instale o 7-Zip ("7z" no PATH) ou compacte como .zip.')
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return redirect('importar-sigtap')
            else:
                messages.error(request, 'Formato não suportado. Envie .rar ou .zip.')
                shutil.rmtree(temp_dir, ignore_errors=True)
                return redirect('importar-sigtap')

            # Reutilizar o importador do management command
            from regulacao.management.commands.import_sigtap_exames import _find_table_file, _read_table_flexible, _detect_columns, _norm
            # transaction already imported at module level

            proc_path = _find_table_file(extract_dir, 'tb_procedimento')
            if not proc_path:
                messages.error(request, 'Arquivo tb_procedimento não encontrado no pacote.')
                shutil.rmtree(temp_dir, ignore_errors=True)
                return redirect('importar-sigtap')

            header, data = _read_table_flexible(proc_path, encoding=encoding)
            if not data:
                messages.error(request, 'tb_procedimento vazio ou inválido.')
                shutil.rmtree(temp_dir, ignore_errors=True)
                return redirect('importar-sigtap')

            i_cod, i_nome, i_grup = _detect_columns(header, data)
            if i_cod is None or i_nome is None:
                preview = data[0] if data else []
                messages.error(request, 'Colunas CO_PROCEDIMENTO/NO_PROCEDIMENTO não encontradas. Envie pacote com cabeçalho (CSV/TXT) ou .zip. Prévia: ' + ' | '.join(preview))
                shutil.rmtree(temp_dir, ignore_errors=True)
                return redirect('importar-sigtap')

            # Valores (opcional)
            valores = {}
            if set_valor:
                val_path = _find_table_file(extract_dir, 'tb_procedimento_valor')
                if val_path:
                    from regulacao.management.commands.import_sigtap_exames import _parse_valor_line_fallback
                    vhead, vrows = _read_table_flexible(val_path, encoding=encoding)
                    vmap = { _norm(h): idx for idx, h in enumerate(vhead) }
                    j_cod = vmap.get('CO_PROCEDIMENTO')
                    j_comp = vmap.get('CO_COMPETENCIA') or vmap.get('DT_COMPETENCIA')
                    j_sh = vmap.get('VL_SH')
                    j_sa = vmap.get('VL_SA')
                    j_sp = vmap.get('VL_SP')
                    by_code = {}
                    if j_cod is not None:
                        for r in vrows:
                            try:
                                code = (r[j_cod] or '').strip()
                                comp = (r[j_comp] or '').strip() if j_comp is not None else ''
                                def p(i):
                                    try:
                                        return float((r[i] or '0').replace(',', '.')) if i is not None else 0.0
                                    except Exception:
                                        return 0.0
                                total = p(j_sh) + p(j_sa) + p(j_sp)
                                prev = by_code.get(code)
                                if not prev or comp > prev[0]:
                                    by_code[code] = (comp, total)
                            except Exception:
                                continue
                    else:
                        # Fallback: ler linha a linha e aplicar heurística
                        try:
                            with open(val_path, 'r', encoding=encoding, newline='') as f:
                                for line in f:
                                    parsed = _parse_valor_line_fallback(line)
                                    if not parsed:
                                        continue
                                    code, comp, total = parsed
                                    prev = by_code.get(code)
                                    if not prev or comp > prev[0]:
                                        by_code[code] = (comp, total)
                        except Exception:
                            messages.warning(request, 'Falha no fallback de parsing de valores; valores não serão atualizados.')
                    valores = { k: v for k, (_, v) in by_code.items() }

            # Filtros
            only_groups_set = {_norm(x) for x in (only_groups.split(',') if only_groups else []) if x.strip()}
            name_terms = [_norm(x) for x in (name_contains.split(',') if name_contains else []) if x.strip()]

            created = 0
            updated = 0
            skipped = 0
            with transaction.atomic():
                for row in data:
                    try:
                        cod = (row[i_cod] or '').strip()
                        nome = (row[i_nome] or '').strip()
                        grupo = (row[i_grup] or '').strip() if i_grup is not None else ''
                    except Exception:
                        skipped += 1
                        continue

                    if not cod or not nome:
                        skipped += 1
                        continue

                    if not grupo and cod:
                        grupo = cod[:2]
                    if only_groups_set and _norm(grupo) not in only_groups_set:
                        continue
                    if name_terms and not any(term in _norm(nome) for term in name_terms):
                        continue

                    obj, is_created = TipoExame.objects.get_or_create(codigo_sus=cod, defaults={
                        'nome': nome,
                        'codigo': cod,
                        'ativo': True,
                    })
                    changed = False
                    if not is_created:
                        if obj.nome != nome:
                            obj.nome = nome
                            changed = True
                        if not obj.codigo:
                            obj.codigo = cod
                            changed = True
                        if not obj.ativo:
                            obj.ativo = True
                            changed = True
                    if set_valor and cod in valores:
                        try:
                            val = float(valores[cod])
                            # TipoExame.valor é DecimalField; atribuição float é aceita, mas podemos converter via str
                            if obj.valor != val:
                                obj.valor = val
                                changed = True
                        except Exception:
                            pass
                    if is_created:
                        obj.save()
                        created += 1
                    elif changed:
                        obj.save()
                        updated += 1

            messages.success(request, f'Importação concluída. Criados: {created}, Atualizados: {updated}, Ignorados: {skipped}.')
            shutil.rmtree(temp_dir, ignore_errors=True)
            return redirect('tipo-exame-list')
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            messages.error(request, f'Falha na importação: {e}')
            return redirect('importar-sigtap')

    return render(request, 'regulacao/importar_sigtap.html', {
        'form': form,
    })
