from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from secretaria_it.access import AccessRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from secretaria_it.access import require_access
from secretaria_it.access import is_ubs_user
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.forms import modelformset_factory
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame, Especialidade, RegulacaoConsulta
from pacientes.models import Paciente
from django.http import JsonResponse
from django.utils import timezone
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
from functools import wraps


# ==== Helpers de Grupo/Permissão ====

def _in_group(user, group_name: str) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())


def require_group(group_name: str):
    """Decorator para exigir um grupo específico."""
    return user_passes_test(lambda u: _in_group(u, group_name))


class GroupRequiredMixin(LoginRequiredMixin):
    """(Desativado) Mantido por compatibilidade; não aplica restrições de grupo."""
    pass


def require_any_group(*group_names: str):
    """Decorator: permite acesso se o usuário estiver em qualquer um dos grupos listados."""
    return user_passes_test(lambda u: any(_in_group(u, g) for g in group_names))


# Versões “amigáveis”: assumem que @login_required vem antes e, se faltar permissão,
# redirecionam para o dashboard (evita loop de login quando usuário autenticado não tem grupo)
def group_required(group_name: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not _in_group(request.user, group_name):
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def any_group_required(*group_names: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not any(_in_group(request.user, g) for g in group_names):
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ============ VIEWS PARA UBS ============

class UBSListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = UBS
    template_name = 'regulacao/ubs_list.html'
    context_object_name = 'ubs_list'
    ordering = ['nome']


class UBSCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = UBS
    form_class = UBSForm
    template_name = 'regulacao/ubs_form.html'
    success_url = reverse_lazy('ubs-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'UBS cadastrada com sucesso!')
        return super().form_valid(form)


class UBSUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = UBS
    form_class = UBSForm
    template_name = 'regulacao/ubs_form.html'
    success_url = reverse_lazy('ubs-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'UBS atualizada com sucesso!')
        return super().form_valid(form)


class UBSDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = UBS
    template_name = 'regulacao/ubs_confirm_delete.html'
    success_url = reverse_lazy('ubs-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'UBS excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA MÉDICOS ============

class MedicoListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoSolicitante
    template_name = 'regulacao/medicosolicitante_list.html'
    context_object_name = 'medico_list'
    ordering = ['nome']


class MedicoCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoSolicitante
    form_class = MedicoSolicitanteForm
    template_name = 'regulacao/medicosolicitante_form.html'
    success_url = reverse_lazy('medico-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Médico cadastrado com sucesso!')
        return super().form_valid(form)


class MedicoUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoSolicitante
    form_class = MedicoSolicitanteForm
    template_name = 'regulacao/medicosolicitante_form.html'
    success_url = reverse_lazy('medico-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Médico atualizado com sucesso!')
        return super().form_valid(form)


class MedicoDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoSolicitante
    template_name = 'regulacao/medicosolicitante_confirm_delete.html'
    success_url = reverse_lazy('medico-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Médico excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA TIPOS DE EXAMES ============

class TipoExameListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = TipoExame
    template_name = 'regulacao/tipoexame_list.html'
    context_object_name = 'tipoexame_list'
    ordering = ['nome']
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().order_by('nome')
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q) |
                Q(codigo__icontains=q) |
                Q(codigo_sus__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = (self.request.GET.get('q') or '').strip()
        return context


class TipoExameCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'regulacao/tipoexame_form.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de exame cadastrado com sucesso!')
        return super().form_valid(form)


class TipoExameUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = TipoExame
    form_class = TipoExameForm
    template_name = 'regulacao/tipoexame_form.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de exame atualizado com sucesso!')
        return super().form_valid(form)


class TipoExameDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = TipoExame
    template_name = 'regulacao/tipoexame_confirm_delete.html'
    success_url = reverse_lazy('tipo-exame-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de exame excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA REGULAÇÃO DE EXAMES ============

class RegulacaoListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = RegulacaoExame
    template_name = 'regulacao/regulacaoexame_list.html'
    context_object_name = 'regulacaoexame_list'
    paginate_by = 20
    
    def get_queryset(self):
        qs = RegulacaoExame.objects.select_related('paciente', 'ubs_solicitante', 'medico_solicitante', 'tipo_exame')

        # Se usuário for UBS, restringir à sua própria UBS
        ubs_user = getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            qs = qs.filter(ubs_solicitante=ubs_user)

        # Aplicar filtros
        status = (self.request.GET.get('status') or '').strip()
        ubs = (self.request.GET.get('ubs') or '').strip()
        tipo = (self.request.GET.get('tipo_exame') or '').strip()
        q = (self.request.GET.get('q') or '').strip()
        data_inicio = (self.request.GET.get('data_inicio') or '').strip()
        data_fim = (self.request.GET.get('data_fim') or '').strip()

        if status:
            if status == 'agendados':
                qs = qs.filter(status='autorizado', data_agendada__isnull=False)
            else:
                qs = qs.filter(status=status)
        if ubs:
            try:
                qs = qs.filter(ubs_solicitante_id=int(ubs))
            except (TypeError, ValueError):
                pass
        if tipo:
            try:
                qs = qs.filter(tipo_exame_id=int(tipo))
            except (TypeError, ValueError):
                pass
        if q:
            qs = qs.filter(
                Q(paciente__nome__icontains=q) |
                Q(paciente__cpf__icontains=q) |
                Q(paciente__cns__icontains=q)
            )
        if data_inicio:
            qs = qs.filter(data_solicitacao__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_solicitacao__date__lte=data_fim)

        return qs.order_by('-data_solicitacao')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ubs_list'] = UBS.objects.filter(ativa=True).order_by('nome')
        context['tipoexame_list'] = TipoExame.objects.filter(ativo=True).order_by('nome')
        context['current_status'] = (self.request.GET.get('status') or '').strip()
        context['current_ubs'] = (self.request.GET.get('ubs') or '').strip()
        context['current_tipo_exame'] = (self.request.GET.get('tipo_exame') or '').strip()
        context['q'] = (self.request.GET.get('q') or '').strip()
        hoje = timezone.localdate()
        context['hoje'] = hoje

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
                    # Situação agregada
                    'fila_count': 0,
                    'pendente_count': 0,
                    'vencidas_count': 0,   # autorizadas com data < hoje
                    'futuras_count': 0,    # autorizadas com data >= hoje
                }
            g = grupos[pid]
            g['total_exames'] += 1
            if reg.tipo_exame and reg.tipo_exame.nome not in g['exames_nomes']:
                g['exames_nomes'].append(reg.tipo_exame.nome)
            if reg.data_solicitacao and reg.data_solicitacao < g['primeira_hora']:
                g['primeira_hora'] = reg.data_solicitacao
            # Atualizar contadores de situação
            if reg.status == 'fila':
                g['fila_count'] += 1
            elif reg.status == 'pendente':
                g['pendente_count'] += 1
            elif reg.status == 'autorizado':
                if reg.data_agendada:
                    if reg.data_agendada < hoje:
                        g['vencidas_count'] += 1
                    else:
                        g['futuras_count'] += 1

        pacientes_grouped = sorted(grupos.values(), key=lambda x: (x['paciente'].nome or '').lower())

        # Paginar os pacientes agrupados usando o mesmo parâmetro de página
        page = self.request.GET.get('page') or 1
        paginator = Paginator(pacientes_grouped, self.paginate_by or 20)
        pacientes_page = paginator.get_page(page)

        context['pacientes_page'] = pacientes_page
        context['paginator'] = paginator
        context['mostrando_agrupado'] = True
        return context


class RegulacaoCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = RegulacaoExame
    form_class = RegulacaoExameCreateForm
    template_name = 'regulacao/regulacaoexame_form.html'
    success_url = reverse_lazy('regulacao-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passar request para que o form consiga aplicar as regras de UBS do usuário
        kwargs['request'] = self.request
        return kwargs
    
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
        # Bloquear criação para tipos já existentes em fila/autorizado para o mesmo paciente,
        # porém permitir se a autorização anterior já passou da data agendada.
        from django.utils import timezone
        hoje = timezone.localdate()
        conflitos_qs = (
            RegulacaoExame.objects
            .filter(paciente=cleaned['paciente'], tipo_exame__in=tipos)
            .filter(
                Q(status='fila') |
                (Q(status='autorizado') & (Q(data_agendada__isnull=True) | Q(data_agendada__gte=hoje)))
            )
            .values('tipo_exame_id', 'tipo_exame__nome', 'status')
            .distinct()
        )
        bloqueados_ids = {c['tipo_exame_id'] for c in conflitos_qs}
        bloqueados_nomes = sorted({c['tipo_exame__nome'] for c in conflitos_qs if c['tipo_exame__nome']})
        tipos_permitidos = [t for t in tipos if t.id not in bloqueados_ids]

        if not tipos_permitidos:
            # Nada a criar: informar conflitos e invalidar o formulário
            if bloqueados_nomes:
                form.add_error('tipos_exame',
                               f"Paciente já possui em fila/autorizado: {', '.join(bloqueados_nomes)}.")
            return self.form_invalid(form)

        created = []
        with transaction.atomic():
            for tipo in tipos_permitidos:
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
        # Mensagens de retorno
        if created:
            messages.success(self.request, f"Solicitação criada com {len(created)} exame(s) no pedido {numero_pedido}.")
        if bloqueados_nomes:
            messages.warning(
                self.request,
                'Alguns exames foram ignorados pois já existem para este paciente em fila ou com agendamento futuro. '
                f"Itens: {', '.join(bloqueados_nomes)}. Caso a data agendada já tenha passado, será possível solicitar novamente."
            )
        # Redireciona para a lista; poderíamos direcionar para o detalhe do primeiro
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        print(f"DEBUG RegulacaoCreateView: Formulário inválido! Erros: {form.errors}")
        messages.error(self.request, 'Por favor, corrija os erros no formulário.')
        return super().form_invalid(form)

    # Observação: Regulação também pode criar solicitações se necessário pelo fluxo


class RegulacaoDetailView(AccessRequiredMixin, LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = RegulacaoExame
    template_name = 'regulacao/regulacao_detail.html'
    context_object_name = 'regulacao'


class RegulacaoUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = RegulacaoExame
    form_class = RegulacaoExameForm
    template_name = 'regulacao/regulacaoexame_form.html'
    success_url = reverse_lazy('regulacao-list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Solicitação atualizada com sucesso! Protocolo: {form.instance.numero_protocolo}')
        return super().form_valid(form)


class RegulacaoDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = RegulacaoExame
    template_name = 'regulacao/regulacaoexame_confirm_delete.html'
    success_url = reverse_lazy('regulacao-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Solicitação de regulação excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# View regular_exame removida: autorização/agendamento passou a ser feito via tela por paciente (paciente_pedido)


@login_required
@require_access('regulacao')
def regular_consulta(request, pk):
    """Redireciona para a tela unificada de autorização por paciente."""
    regulacao = get_object_or_404(RegulacaoConsulta, pk=pk)
    # Mensagem opcional para indicar o novo fluxo
    messages.info(request, 'Fluxo atualizado: autorização é feita na página do paciente.')
    return redirect('paciente-pedido', paciente_id=regulacao.paciente_id)


@login_required
@require_access('regulacao')
def dashboard_regulacao(request):
    """Dashboard da regulação.
    - Para usuários de UBS: exibe um portal simplificado com apenas as ações de solicitação.
    - Para demais perfis: exibe o dashboard completo com estatísticas.
    """
    # Superadmin: ver dashboard completo (sem restrições)
    if request.user.is_superuser:
        # Métricas principais
        total_consultas_autorizadas = RegulacaoConsulta.objects.filter(status='autorizado').count()
        total_autorizados = RegulacaoExame.objects.filter(status='autorizado').count()
        total_pendentes = RegulacaoExame.objects.filter(status='pendente').count()
        total_negados = RegulacaoExame.objects.filter(status='negado').count()

        # Quantidade de pacientes distintos na fila (exames e consultas)
        exames_fila_pacientes = RegulacaoExame.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
        consultas_fila_pacientes = RegulacaoConsulta.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
        pacientes_fila_exames_count = exames_fila_pacientes.count()
        pacientes_fila_consultas_count = consultas_fila_pacientes.count()

        return render(request, 'regulacao/dashboard_full.html', {
            'total_consultas_autorizadas': total_consultas_autorizadas,
            'total_autorizados': total_autorizados,
            'total_pendentes': total_pendentes,
            'total_negados': total_negados,
            'pacientes_fila_exames_count': pacientes_fila_exames_count,
            'pacientes_fila_consultas_count': pacientes_fila_consultas_count,
        })

    # Rota enxuta para usuários de UBS (apenas se não for superadmin)
    ubs_user = getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None)
    if ubs_user:
        return render(request, 'regulacao/portal_ubs.html', {
            'ubs_atual': ubs_user,
        })

    # Quantidade de pacientes distintos na fila (exames e consultas) — usado no dashboard enxuto
    exames_fila_pacientes = RegulacaoExame.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
    consultas_fila_pacientes = RegulacaoConsulta.objects.filter(status='fila').values_list('paciente_id', flat=True).distinct()
    pacientes_fila_exames_count = exames_fila_pacientes.count()
    pacientes_fila_consultas_count = consultas_fila_pacientes.count()

    return render(request, 'regulacao/dashboard.html', {
        'pacientes_fila_exames_count': pacientes_fila_exames_count,
        'pacientes_fila_consultas_count': pacientes_fila_consultas_count,
    })


 


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
        # Se usuário for UBS, restringir à sua própria UBS
        ubs_user = getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            qs = qs.filter(ubs_solicitante=ubs_user)
        status = (self.request.GET.get('status') or '').strip()
        ubs = (self.request.GET.get('ubs') or '').strip()
        espec = (self.request.GET.get('especialidade') or '').strip()
        q = (self.request.GET.get('q') or '').strip()

        # Status filter, including virtual "agendados" (autorizado com data agendada)
        if status:
            if status == 'agendados':
                qs = qs.filter(status='autorizado', data_agendada__isnull=False)
            else:
                qs = qs.filter(status=status)

        if ubs:
            try:
                qs = qs.filter(ubs_solicitante_id=int(ubs))
            except (TypeError, ValueError):
                pass

        if espec:
            try:
                qs = qs.filter(especialidade_id=int(espec))
            except (TypeError, ValueError):
                pass

        if q:
            qs = qs.filter(
                Q(paciente__nome__icontains=q) |
                Q(paciente__cpf__icontains=q) |
                Q(paciente__cns__icontains=q)
            )

        return qs.order_by('-data_solicitacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = (self.request.GET.get('status') or '').strip()
        context['current_ubs'] = (self.request.GET.get('ubs') or '').strip()
        context['current_especialidade'] = (self.request.GET.get('especialidade') or '').strip()
        context['q'] = (self.request.GET.get('q') or '').strip()
        context['ubs_list'] = UBS.objects.filter(ativa=True).order_by('nome')
        context['especialidades'] = Especialidade.objects.filter(ativa=True).order_by('nome')
        from django.utils import timezone
        context['hoje'] = timezone.localdate()
        return context


class RegulacaoConsultaCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    form_class = RegulacaoConsultaForm
    template_name = 'regulacao/regulacaoconsulta_form.html'
    success_url = reverse_lazy('consulta-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passar request para que o form consiga aplicar as regras de UBS do usuário
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        cleaned = form.cleaned_data
        paciente = cleaned.get('paciente')
        especialidade = cleaned.get('especialidade')
        if paciente and especialidade:
            from django.utils import timezone
            hoje = timezone.localdate()
            conflito = (
                RegulacaoConsulta.objects.filter(
                    paciente=paciente,
                    especialidade=especialidade,
                )
                .filter(
                    Q(status='fila') |
                    (Q(status='autorizado') & (Q(data_agendada__isnull=True) | Q(data_agendada__gte=hoje)))
                )
            )
            if getattr(form.instance, 'pk', None):
                conflito = conflito.exclude(pk=form.instance.pk)
            if conflito.exists():
                # Mensagem de alerta para o usuário
                total = conflito.count()
                tem_agendada = conflito.filter(status='autorizado', data_agendada__isnull=False).exists()
                detalhes_list = []
                for r in conflito.select_related('especialidade', 'ubs_solicitante'):
                    espec_nome = r.especialidade.nome if r.especialidade else '—'
                    ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else '—'
                    ag_txt = ''
                    if r.status == 'autorizado' and r.data_agendada:
                        try:
                            ag_txt = f" (agendada para {r.data_agendada.strftime('%d/%m/%Y')}"
                            if r.hora_agendada:
                                ag_txt += f" {r.hora_agendada.strftime('%H:%M')}"
                            ag_txt += ")"
                        except Exception:
                            ag_txt = ''
                    detalhes_list.append(f"{espec_nome} (UBS {ubs_nome}) - {r.get_status_display()}{ag_txt}")
                detalhes_txt = '; '.join(detalhes_list)
                msg = (
                    f"Paciente já possui {total} consulta(s) desta especialidade em fila ou autorizada. "
                    + ("Há consulta agendada nessa especialidade. " if tem_agendada else "")
                    + (f"Detalhes: {detalhes_txt}." if detalhes_txt else "")
                ).strip()
                messages.warning(self.request, msg)
                form.add_error('especialidade', 'Paciente já possui solicitação desta especialidade em fila ou autorizada. ' 
                                               'Conclua ou cancele antes de criar outra.')
                return self.form_invalid(form)

        # Aviso geral: paciente já possui outras consultas (qualquer especialidade) em fila ou agendadas
        if paciente:
            outros = RegulacaoConsulta.objects.filter(paciente=paciente, status__in=['fila', 'autorizado'])
            if especialidade:
                outros = outros.exclude(especialidade=especialidade)
            if outros.exists():
                fila_count = outros.filter(status='fila').count()
                agendadas_count = outros.filter(status='autorizado', data_agendada__isnull=False).count()
                if fila_count or agendadas_count:
                    detalhes_list = []
                    for r in outros.select_related('especialidade', 'ubs_solicitante'):
                        espec_nome = r.especialidade.nome if r.especialidade else '—'
                        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else '—'
                        ag_txt = ''
                        if r.status == 'autorizado' and r.data_agendada:
                            try:
                                ag_txt = f" (agendada para {r.data_agendada.strftime('%d/%m/%Y')}"
                                if r.hora_agendada:
                                    ag_txt += f" {r.hora_agendada.strftime('%H:%M')}"
                                ag_txt += ")"
                            except Exception:
                                ag_txt = ''
                        detalhes_list.append(f"{espec_nome} (UBS {ubs_nome}) - {r.get_status_display()}{ag_txt}")
                    detalhes_txt = '; '.join(detalhes_list)
                    messages.info(
                        self.request,
                        (
                            f"Atenção: este paciente já possui "
                            f"{fila_count} consulta(s) em fila de espera e {agendadas_count} consulta(s) agendada(s). "
                            + (f"Detalhes: {detalhes_txt}." if detalhes_txt else "")
                        )
                    )
        return super().form_valid(form)

    # Observação: Regulação também pode criar solicitações se necessário pelo fluxo


@login_required
@require_access('regulacao')
def consulta_paciente_alertas(request):
    """Retorna contagens de consultas em fila e agendadas para um paciente (JSON).
    Parâmetros GET:
      - paciente_id (obrigatório)
      - especialidade_id (opcional) para informar se já há na mesma especialidade
    """
    try:
        pid = int(request.GET.get('paciente_id') or 0)
    except (TypeError, ValueError):
        pid = 0
    if not pid:
        return JsonResponse({'ok': False, 'error': 'paciente_id ausente'}, status=400)
    espec_id = request.GET.get('especialidade_id')
    try:
        espec_id = int(espec_id) if espec_id else None
    except (TypeError, ValueError):
        espec_id = None

    from django.utils import timezone
    hoje = timezone.localdate()
    base_qs = (
        RegulacaoConsulta.objects.select_related('especialidade', 'ubs_solicitante')
        .filter(paciente_id=pid)
        .filter(
            Q(status='fila') |
            (Q(status='autorizado') & (Q(data_agendada__isnull=True) | Q(data_agendada__gte=hoje)))
        )
    )
    fila_count = base_qs.filter(status='fila').count()
    agendadas_count = base_qs.filter(status='autorizado', data_agendada__isnull=False, data_agendada__gte=hoje).count()

    same_espec = None
    if espec_id:
        same_espec = base_qs.filter(especialidade_id=espec_id).exists()

    # Detalhes por item (especialidade, UBS, status e, se houver, data/hora)
    detalhes = []
    for r in base_qs.order_by('data_solicitacao'):
        espec_nome = r.especialidade.nome if r.especialidade else '-'
        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else '-'
        ag_txt = ''
        if r.status == 'autorizado' and r.data_agendada:
            try:
                ag_txt = f" (agendada para {r.data_agendada.strftime('%d/%m/%Y')}"
                if r.hora_agendada:
                    ag_txt += f" {r.hora_agendada.strftime('%H:%M')}"
                ag_txt += ")"
            except Exception:
                ag_txt = ''
        detalhes.append(f"{espec_nome} (UBS {ubs_nome}) - {r.get_status_display()}{ag_txt}")

    return JsonResponse({
        'ok': True,
        'fila_count': fila_count,
        'agendadas_count': agendadas_count,
        'same_especialidade': bool(same_espec) if same_espec is not None else None,
        'detalhes': detalhes,
    })


@login_required
@require_access('regulacao')
def exame_paciente_alertas(request):
    """Retorna informações sobre exames do paciente para avisos (fila/autorizados e conflitos por tipo).
    GET params:
      - paciente_id (int) obrigatório
      - tipos (csv de ids de tipo_exame) opcional
    """
    try:
        pid = int(request.GET.get('paciente_id') or 0)
    except (TypeError, ValueError):
        pid = 0
    if not pid:
        return JsonResponse({'ok': False, 'error': 'paciente_id ausente'}, status=400)

    tipos_param = (request.GET.get('tipos') or '').strip()
    tipos_ids = set()
    if tipos_param:
        for part in tipos_param.split(','):
            try:
                tipos_ids.add(int(part))
            except (TypeError, ValueError):
                continue

    from django.utils import timezone
    hoje = timezone.localdate()
    base_qs = (
        RegulacaoExame.objects
        .select_related('tipo_exame', 'ubs_solicitante')
        .filter(paciente_id=pid)
        .filter(
            Q(status='fila') |
            (Q(status='autorizado') & (Q(data_agendada__isnull=True) | Q(data_agendada__gte=hoje)))
        )
        .order_by('data_solicitacao')
    )

    fila_count = base_qs.filter(status='fila').count()
    agendadas_count = base_qs.filter(status='autorizado', data_agendada__isnull=False, data_agendada__gte=hoje).count()

    same_tipos = False
    conflitos_tipos = []
    if tipos_ids:
        confl_qs = base_qs.filter(tipo_exame_id__in=tipos_ids)
        same_tipos = confl_qs.exists()
        if same_tipos:
            conflitos_tipos = sorted({r.tipo_exame.nome for r in confl_qs if r.tipo_exame})

    detalhes = []
    for r in base_qs:
        exame_nome = r.tipo_exame.nome if r.tipo_exame else '-'
        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else '-'
        ag_txt = ''
        if r.status == 'autorizado' and r.data_agendada:
            try:
                ag_txt = f" (agendado para {r.data_agendada.strftime('%d/%m/%Y')}"
                if r.hora_agendada:
                    ag_txt += f" {r.hora_agendada.strftime('%H:%M')}"
                ag_txt += ")"
            except Exception:
                ag_txt = ''
        detalhes.append(f"{exame_nome} (UBS {ubs_nome}) - {r.get_status_display()}{ag_txt}")

    return JsonResponse({
        'ok': True,
        'fila_count': fila_count,
        'agendadas_count': agendadas_count,
        'same_tipos': same_tipos,
        'conflitos_tipos': conflitos_tipos,
        'detalhes': detalhes,
    })


class RegulacaoConsultaUpdateView(LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    model = RegulacaoConsulta
    form_class = RegulacaoConsultaForm
    template_name = 'regulacao/regulacaoconsulta_form.html'
    success_url = reverse_lazy('consulta-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passar request para que o form consiga aplicar as regras de UBS do usuário
        kwargs['request'] = self.request
        return kwargs

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


#### Adicionar filtro para consultas na fila de espera
@login_required
@require_access('regulacao')
def fila_espera(request):
    """Fila de espera unificada para exames e consultas (status = fila)."""
    # UBS users não devem acessar a fila completa
    if is_ubs_user(request.user):
        return redirect('regulacao-dashboard')
    q_ex = (request.GET.get('q_ex') or '').strip()
    q_co = (request.GET.get('q_co') or '').strip()
    only = (request.GET.get('only') or '').strip()
    di = (request.GET.get('di') or '').strip()  # data início
    df = (request.GET.get('df') or '').strip()  # data fim
    from django.utils.dateparse import parse_date
    di_d = parse_date(di) if di else None
    df_d = parse_date(df) if df else None

    exames_qs = RegulacaoExame.objects.select_related('paciente', 'tipo_exame', 'ubs_solicitante').filter(status='fila')
    if di_d:
        exames_qs = exames_qs.filter(data_solicitacao__date__gte=di_d)
    if df_d:
        exames_qs = exames_qs.filter(data_solicitacao__date__lte=df_d)
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
    if di_d:
        consultas_qs = consultas_qs.filter(data_solicitacao__date__gte=di_d)
    if df_d:
        consultas_qs = consultas_qs.filter(data_solicitacao__date__lte=df_d)
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
                'ubs': [],   # nomes de UBS solicitantes únicos
            }
        g = grupos_ex[pid]
        g['total'] += 1
        nome = r.tipo_exame.nome if r.tipo_exame else ''
        if nome and nome not in g['nomes']:
            g['nomes'].append(nome)
        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else ''
        if ubs_nome and ubs_nome not in g['ubs']:
            g['ubs'].append(ubs_nome)
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
                'ubs': [],   # nomes de UBS solicitantes únicos
            }
        g = grupos_co[pid]
        g['total'] += 1
        nome = r.especialidade.nome if r.especialidade else ''
        if nome and nome not in g['nomes']:
            g['nomes'].append(nome)
        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else ''
        if ubs_nome and ubs_nome not in g['ubs']:
            g['ubs'].append(ubs_nome)
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
        'di': di,
        'df': df,
    })


@login_required
@require_access('regulacao')
def agenda_regulacao(request):
    """Agenda da regulação: itens autorizados com data/hora agendadas."""
    # Utilitário local para parse de datas em filtros
    from django.utils.dateparse import parse_date
    from django.utils import timezone
    # Se usuário for UBS, restringir agenda à sua própria UBS
    ubs_user = getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None)
    exames_qs = RegulacaoExame.objects.select_related('paciente', 'tipo_exame', 'ubs_solicitante').filter(
        status='autorizado', data_agendada__isnull=False
    )
    consultas_qs = RegulacaoConsulta.objects.select_related('paciente', 'especialidade', 'ubs_solicitante').filter(
        status='autorizado', data_agendada__isnull=False
    )

    # Filtros de data (agenda principal)
    hoje = timezone.localdate()
    di = (request.GET.get('di') or '').strip()
    df = (request.GET.get('df') or '').strip()
    di_d = parse_date(di) if di else None
    df_d = parse_date(df) if df else None
    # Se não houver data inicial, usar hoje como padrão
    if not di_d:
        di_d = hoje
        di = hoje.isoformat()
    # Se não houver data final, usar hoje como padrão
    if not df_d:
        df_d = hoje
        df = hoje.isoformat()
    if di_d:
        exames_qs = exames_qs.filter(data_agendada__gte=di_d)
        consultas_qs = consultas_qs.filter(data_agendada__gte=di_d)
    if df_d:
        exames_qs = exames_qs.filter(data_agendada__lte=df_d)
        consultas_qs = consultas_qs.filter(data_agendada__lte=df_d)
    if ubs_user:
        exames_qs = exames_qs.filter(ubs_solicitante=ubs_user)
        consultas_qs = consultas_qs.filter(ubs_solicitante=ubs_user)
    exames = exames_qs.order_by('data_agendada', 'hora_agendada')
    consultas = consultas_qs.order_by('data_agendada', 'hora_agendada')
    only = (request.GET.get('only') or '').strip()
    context = {
        'exames': exames,
        'consultas': consultas,
        'ubs_atual': ubs_user,
        # filtros agenda
        'di': di,
        'df': df,
        'hoje': hoje,
        'only': only,
    }
    # Para usuários de UBS, incluir também itens pendentes (fila/pendente) apenas para visualização
    if ubs_user:
        pend_ex = RegulacaoExame.objects.select_related('paciente','tipo_exame').filter(
            ubs_solicitante=ubs_user, status__in=['fila','pendente']
        ).order_by('-data_solicitacao')
        pend_co = RegulacaoConsulta.objects.select_related('paciente','especialidade').filter(
            ubs_solicitante=ubs_user, status__in=['fila','pendente']
        ).order_by('-data_solicitacao')

        # Filtros Consultas pendentes (pco)
        q_pco = (request.GET.get('q_pco') or '').strip()
        di_pco = (request.GET.get('di_pco') or '').strip()
        df_pco = (request.GET.get('df_pco') or '').strip()
        s_pco = parse_date(di_pco) if di_pco else None
        e_pco = parse_date(df_pco) if df_pco else None
        if q_pco:
            pend_co = pend_co.filter(
                Q(paciente__nome__icontains=q_pco) |
                Q(especialidade__nome__icontains=q_pco)
            )
        if s_pco:
            pend_co = pend_co.filter(data_solicitacao__date__gte=s_pco)
        if e_pco:
            pend_co = pend_co.filter(data_solicitacao__date__lte=e_pco)

        # Filtros Exames pendentes (pex)
        q_pex = (request.GET.get('q_pex') or '').strip()
        di_pex = (request.GET.get('di_pex') or '').strip()
        df_pex = (request.GET.get('df_pex') or '').strip()
        s_pex = parse_date(di_pex) if di_pex else None
        e_pex = parse_date(df_pex) if df_pex else None
        if q_pex:
            pend_ex = pend_ex.filter(
                Q(paciente__nome__icontains=q_pex) |
                Q(tipo_exame__nome__icontains=q_pex)
            )
        if s_pex:
            pend_ex = pend_ex.filter(data_solicitacao__date__gte=s_pex)
        if e_pex:
            pend_ex = pend_ex.filter(data_solicitacao__date__lte=e_pex)

        # Paginação
        def _to_int(val, default, min_v=1, max_v=200):
            try:
                n = int(val)
                return max(min_v, min(n, max_v))
            except (TypeError, ValueError):
                return default
        per_pco = _to_int(request.GET.get('per_pco'), 10)
        per_pex = _to_int(request.GET.get('per_pex'), 10)
        page_pco = request.GET.get('page_pco') or 1
        page_pex = request.GET.get('page_pex') or 1
        p_pco = Paginator(pend_co, per_pco)
        p_pex = Paginator(pend_ex, per_pex)
        pend_co_page = p_pco.get_page(page_pco)
        pend_ex_page = p_pex.get_page(page_pex)

        # Helper para montar querystring sem certos parâmetros
        from django.utils.http import urlencode
        def build_qs_without(exclude_keys: set):
            params = []
            for k in request.GET.keys():
                if k in exclude_keys:
                    continue
                for v in request.GET.getlist(k):
                    params.append((k, v))
            return urlencode(params)

        # Exames Negados (UBS): permitir ver e entender o motivo
        neg_ex = RegulacaoExame.objects.select_related('paciente','tipo_exame').filter(
            ubs_solicitante=ubs_user, status='negado'
        ).order_by('-data_solicitacao')
        q_nex = (request.GET.get('q_nex') or '').strip()
        di_nex = (request.GET.get('di_nex') or '').strip()
        df_nex = (request.GET.get('df_nex') or '').strip()
        s_nex = parse_date(di_nex) if di_nex else None
        e_nex = parse_date(df_nex) if df_nex else None
        if q_nex:
            neg_ex = neg_ex.filter(
                Q(paciente__nome__icontains=q_nex) |
                Q(tipo_exame__nome__icontains=q_nex) |
                Q(motivo_decisao__icontains=q_nex)
            )
        if s_nex:
            neg_ex = neg_ex.filter(data_solicitacao__date__gte=s_nex)
        if e_nex:
            neg_ex = neg_ex.filter(data_solicitacao__date__lte=e_nex)
        per_nex = _to_int(request.GET.get('per_nex'), 10)
        page_nex = request.GET.get('page_nex') or 1
        p_nex = Paginator(neg_ex, per_nex)
        neg_ex_page = p_nex.get_page(page_nex)

        context.update({
            'pend_co_page': pend_co_page,
            'pend_ex_page': pend_ex_page,
            'qs_pco': build_qs_without({'page_pco'}),
            'qs_pex': build_qs_without({'page_pex'}),
            'q_pco': q_pco, 'di_pco': di_pco, 'df_pco': df_pco, 'per_pco': per_pco,
            'q_pex': q_pex, 'di_pex': di_pex, 'df_pex': df_pex, 'per_pex': per_pex,
            'pend_exames': pend_ex,  # ainda disponível se necessário
            'pend_consultas': pend_co,
            # Negados
            'neg_ex_page': neg_ex_page,
            'q_nex': q_nex, 'di_nex': di_nex, 'df_nex': df_nex, 'per_nex': per_nex,
            'qs_nex': build_qs_without({'page_nex'}),
        })
    return render(request, 'regulacao/agenda.html', context)


@login_required
@require_access('regulacao')
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
@require_access('regulacao')
def comprovante_exame(request, pk: int):
    reg = get_object_or_404(RegulacaoExame.objects.select_related('paciente','tipo_exame','ubs_solicitante','medico_atendente'), pk=pk)
    qr = _qrcode_base64(reg.numero_protocolo)
    return render(request, 'regulacao/comprovante_exame.html', {
        'reg': reg,
        'qr_base64': qr,
    })

@login_required
@require_access('regulacao')
def comprovante_consulta(request, pk: int):
    reg = get_object_or_404(RegulacaoConsulta.objects.select_related('paciente','especialidade','ubs_solicitante','medico_atendente'), pk=pk)
    qr = _qrcode_base64(reg.numero_protocolo)
    return render(request, 'regulacao/comprovante_consulta.html', {
        'reg': reg,
        'qr_base64': qr,
    })

@login_required
@require_access('regulacao')
def comprovantes_exames(request):
    """Imprime múltiplos comprovantes de exames autorizados.
    - Se "ids" estiver no querystring, filtra por esses IDs.
    - Agrupa por data_agendada (data) e imprime todos do mesmo dia juntos.
    """
    qs = RegulacaoExame.objects.select_related('paciente','tipo_exame','ubs_solicitante','medico_atendente').filter(status='autorizado')
    ids = request.GET.get('ids')
    if ids:
        ids_list = [int(x) for x in ids.split(',') if x.isdigit()]
        qs = qs.filter(id__in=ids_list)
    from collections import defaultdict
    grupos = defaultdict(list)
    for reg in qs.order_by('data_agendada','hora_agendada','id'):
        dia = reg.data_agendada or None
        grupos[dia].append(reg)
    # Ordenar por data (None por último)
    chaves = sorted(grupos.keys(), key=lambda d: (d is None, d))
    grupos_ordenados = [(k, grupos[k]) for k in chaves]
    return render(request, 'regulacao/comprovantes_exames.html', {
        'grupos': grupos_ordenados,
        'qtd': qs.count(),
        'show_details': request.GET.get('detalhes') in ('1','true','True','sim','yes'),
    })

@login_required
@require_access('regulacao')
def comprovantes_consultas(request):
    """Imprime múltiplos comprovantes de consultas autorizadas; aceita filtro por "ids"."""
    qs = RegulacaoConsulta.objects.select_related('paciente','especialidade','ubs_solicitante','medico_atendente').filter(status='autorizado')
    ids = request.GET.get('ids')
    if ids:
        ids_list = [int(x) for x in ids.split(',') if x.isdigit()]
        qs = qs.filter(id__in=ids_list)
    qs = qs.order_by('data_agendada','hora_agendada','id')
    return render(request, 'regulacao/comprovantes_consultas.html', {
        'regs': list(qs),
        'qtd': qs.count(),
        'show_details': request.GET.get('detalhes') in ('1','true','True','sim','yes'),
    })


# ============ Resultado de Atendimento (Compareceu/Faltou) ============

@login_required
@require_access('regulacao')
def registrar_resultado_exame(request, pk: int):
    if request.method != 'POST':
        return redirect('regulacao-agenda')
    reg = get_object_or_404(RegulacaoExame, pk=pk)
    # somente para autorizados com data agendada
    if reg.status != 'autorizado' or not reg.data_agendada:
        messages.error(request, 'Somente itens autorizados e com data agendada podem receber resultado.')
        return redirect(_back_to_agenda(request))
    hoje = timezone.localdate()
    if reg.data_agendada > hoje:
        messages.error(request, 'Não é possível registrar resultado antes da data agendada.')
        return redirect(_back_to_agenda(request))
    val = (request.POST.get('resultado') or '').strip()
    obs = (request.POST.get('observacao') or '').strip()
    if val not in ('compareceu', 'faltou', 'pendente'):
        messages.error(request, 'Resultado inválido.')
        return redirect(_back_to_agenda(request))
    reg.resultado_atendimento = val
    reg.resultado_observacao = obs
    reg.resultado_por = request.user
    reg.resultado_em = timezone.now()
    reg.save(update_fields=['resultado_atendimento','resultado_observacao','resultado_por','resultado_em','atualizado_em'])
    messages.success(request, 'Resultado do atendimento registrado.')
    return redirect(_back_to_agenda(request, default_only='ex', default_hash='#exames-pane'))


@login_required
@require_access('regulacao')
def registrar_resultado_consulta(request, pk: int):
    if request.method != 'POST':
        return redirect('regulacao-agenda')
    reg = get_object_or_404(RegulacaoConsulta, pk=pk)
    if reg.status != 'autorizado' or not reg.data_agendada:
        messages.error(request, 'Somente itens autorizados e com data agendada podem receber resultado.')
        return redirect(_back_to_agenda(request))
    hoje = timezone.localdate()
    if reg.data_agendada > hoje:
        messages.error(request, 'Não é possível registrar resultado antes da data agendada.')
        return redirect(_back_to_agenda(request))
    val = (request.POST.get('resultado') or '').strip()
    obs = (request.POST.get('observacao') or '').strip()
    if val not in ('compareceu', 'faltou', 'pendente'):
        messages.error(request, 'Resultado inválido.')
        return redirect(_back_to_agenda(request))
    reg.resultado_atendimento = val
    reg.resultado_observacao = obs
    reg.resultado_por = request.user
    reg.resultado_em = timezone.now()
    reg.save(update_fields=['resultado_atendimento','resultado_observacao','resultado_por','resultado_em','atualizado_em'])
    messages.success(request, 'Resultado do atendimento registrado.')
    return redirect(_back_to_agenda(request, default_only='co', default_hash='#consultas-pane'))


def _back_to_agenda(request, default_only: str | None = None, default_hash: str = '') -> str:
    """Monta uma URL de retorno à agenda preservando filtros e aba."""
    base = '/regulacao/agenda/'
    from django.utils.http import urlencode
    params = []
    for k in request.GET.keys():
        for v in request.GET.getlist(k):
            params.append((k, v))
    # Se não há "only" e foi fornecido um default, usar
    if default_only and not any(k == 'only' for k, _ in params):
        params.append(('only', default_only))
    qs = urlencode(params)
    if qs:
        return f"{base}?{qs}{default_hash}"
    return f"{base}{default_hash}"

@login_required
@require_access('regulacao')
def paciente_pedido(request, paciente_id):
    """Página única por paciente para listar todas as solicitações e autorizar/agendar seleções."""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    # UBS: somente visualização; não pode autorizar/
    read_only = is_ubs_user(request.user)
    # Exames do paciente (todos para contexto; foco em fila/pendente para autorizar)
    exames_qs = RegulacaoExame.objects.select_related('tipo_exame', 'ubs_solicitante', 'medico_solicitante').filter(paciente=paciente).order_by('-data_solicitacao')
    exames_pendentes_qs = exames_qs.filter(status__in=['fila', 'pendente'])

    # Consultas do paciente
    consultas_qs = RegulacaoConsulta.objects.select_related('especialidade', 'ubs_solicitante', 'medico_solicitante').filter(paciente=paciente).order_by('-data_solicitacao')
    consultas_pendentes_qs = consultas_qs.filter(status__in=['fila', 'pendente'])

    ExameFormSet = modelformset_factory(RegulacaoExame, form=RegulacaoExameBatchForm, extra=0, can_delete=False)
    ConsultaFormSet = modelformset_factory(RegulacaoConsulta, form=RegulacaoConsultaBatchForm, extra=0, can_delete=False)

    if request.method == 'POST':
        if read_only:
            messages.error(request, 'Usuários de UBS não podem autorizar ou negar solicitações. Acesso somente para visualização.')
            return redirect('paciente-pedido', paciente_id=paciente.id)
        submitted_exames = 'submit_exames' in request.POST or 'deny_exames' in request.POST
        submitted_consultas = 'submit_consultas' in request.POST or 'deny_consultas' in request.POST
        exame_fs = ExameFormSet(request.POST if submitted_exames else None, queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(request.POST if submitted_consultas else None, queryset=consultas_pendentes_qs, prefix='co')
        # Anexar request aos forms (para validação contextual)
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            setattr(f, 'request', request)

        # Processar apenas o formset submetido
        from django.utils import timezone
        if submitted_exames:
            if exame_fs.is_valid():
                aprovados_exames = 0
                negados_exames = 0
                aprovados_ids = []
                # Verificar conflitos de agenda por data (antes de salvar)
                datas_selecionadas = set()
                for form in exame_fs.forms:
                    if form.cleaned_data.get('autorizar'):
                        d = form.cleaned_data.get('data_agendada')
                        if d:
                            datas_selecionadas.add(d)
                conflitos_por_data = {}
                if datas_selecionadas:
                    for d in sorted(datas_selecionadas):
                        ex_count = RegulacaoExame.objects.filter(paciente=paciente, status='autorizado', data_agendada=d).count()
                        co_count = RegulacaoConsulta.objects.filter(paciente=paciente, status='autorizado', data_agendada=d).count()
                        total = ex_count + co_count
                        if total > 0:
                            conflitos_por_data[d] = (ex_count, co_count, total)
                with transaction.atomic():
                    for form in exame_fs.forms:
                        inst = form.instance
                        if form.cleaned_data.get('autorizar'):
                            inst.status = 'autorizado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # Ambos os perfis podem agendar ao autorizar
                            inst.local_realizacao = form.cleaned_data.get('local_realizacao')
                            inst.data_agendada = form.cleaned_data.get('data_agendada')
                            inst.hora_agendada = form.cleaned_data.get('hora_agendada')
                            # médico atendente removido do fluxo de exames
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            aprovados_exames += 1
                            aprovados_ids.append(inst.id)
                        elif form.cleaned_data.get('negar'):
                            inst.status = 'negado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # limpar dados de agendamento ao negar
                            inst.local_realizacao = ''
                            inst.data_agendada = None
                            inst.hora_agendada = None
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            negados_exames += 1
                if aprovados_exames:
                    messages.success(request, f"{aprovados_exames} exame(s) autorizados e agendados para {paciente.nome}.")
                    # Exibir avisos de conflitos encontrados
                    for d, (ex_count, co_count, total) in conflitos_por_data.items():
                        messages.warning(request, (
                            f"Atenção: {paciente.nome} já possui {total} compromisso(s) nessa data {d:%d/%m/%Y} "
                            f"({ex_count} exame(s), {co_count} consulta(s))."
                        ))
                if negados_exames:
                    messages.warning(request, f"{negados_exames} exame(s) negados para {paciente.nome}.")
                if not aprovados_exames and not negados_exames:
                    messages.info(request, 'Nenhum exame marcado para autorização.')
                return redirect('paciente-pedido', paciente_id=paciente.id)
            else:
                messages.error(request, 'Corrija os erros nos exames para prosseguir.')

        if submitted_consultas:
            if consulta_fs.is_valid():
                aprovados_consultas = 0
                negadas_consultas = 0
                aprovados_ids = []
                # Verificar conflitos de agenda por data (antes de salvar)
                datas_selecionadas = set()
                for form in consulta_fs.forms:
                    if form.cleaned_data.get('autorizar'):
                        d = form.cleaned_data.get('data_agendada')
                        if d:
                            datas_selecionadas.add(d)
                conflitos_por_data = {}
                if datas_selecionadas:
                    for d in sorted(datas_selecionadas):
                        ex_count = RegulacaoExame.objects.filter(paciente=paciente, status='autorizado', data_agendada=d).count()
                        co_count = RegulacaoConsulta.objects.filter(paciente=paciente, status='autorizado', data_agendada=d).count()
                        total = ex_count + co_count
                        if total > 0:
                            conflitos_por_data[d] = (ex_count, co_count, total)
                with transaction.atomic():
                    for form in consulta_fs.forms:
                        inst = form.instance
                        if form.cleaned_data.get('autorizar'):
                            inst.status = 'autorizado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # Ambos os perfis podem agendar ao autorizar
                            inst.local_atendimento = form.cleaned_data.get('local_atendimento')
                            inst.data_agendada = form.cleaned_data.get('data_agendada')
                            inst.hora_agendada = form.cleaned_data.get('hora_agendada')
                            # médico atendente permanece para consultas
                            inst.medico_atendente = form.cleaned_data.get('medico_atendente')
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            aprovados_consultas += 1
                            aprovados_ids.append(inst.id)
                        elif form.cleaned_data.get('negar'):
                            inst.status = 'negado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # limpar dados de agendamento ao negar
                            inst.local_atendimento = ''
                            inst.data_agendada = None
                            inst.hora_agendada = None
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            negadas_consultas += 1
                if aprovados_consultas:
                    messages.success(request, f"{aprovados_consultas} consulta(s) autorizadas e agendadas para {paciente.nome}.")
                    # Exibir avisos de conflitos encontrados
                    for d, (ex_count, co_count, total) in conflitos_por_data.items():
                        messages.warning(request, (
                            f"Atenção: {paciente.nome} já possui {total} compromisso(s) nessa data {d:%d/%m/%Y} "
                            f"({ex_count} exame(s), {co_count} consulta(s))."
                        ))
                if negadas_consultas:
                    messages.warning(request, f"{negadas_consultas} consulta(s) negadas para {paciente.nome}.")
                if not aprovados_consultas and not negadas_consultas:
                    messages.info(request, 'Nenhuma consulta marcada para autorização.')
                return redirect('paciente-pedido', paciente_id=paciente.id)
            else:
                messages.error(request, 'Corrija os erros nas consultas para prosseguir.')
    else:
        exame_fs = ExameFormSet(queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(queryset=consultas_pendentes_qs, prefix='co')
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            setattr(f, 'request', request)
        if 'medico_atendente' in consulta_fs.empty_form.fields:
            consulta_fs.empty_form.fields['medico_atendente'].queryset = MedicoSolicitante.objects.filter(ativo=True).order_by('nome')
        for f in consulta_fs.forms:
            if 'medico_atendente' in f.fields:
                f.fields['medico_atendente'].queryset = MedicoSolicitante.objects.filter(ativo=True).order_by('nome')

    # IDs autorizados (para botões de impressão)
    exames_aut_ids = list(exames_qs.filter(status='autorizado').values_list('id', flat=True))
    consultas_aut_ids = list(consultas_qs.filter(status='autorizado').values_list('id', flat=True))
    exames_aut_ids_csv = ','.join(str(i) for i in exames_aut_ids)
    consultas_aut_ids_csv = ','.join(str(i) for i in consultas_aut_ids)

    return render(request, 'regulacao/paciente_pedido.html', {
        'paciente': paciente,
        'exame_formset': exame_fs,
        'consulta_formset': consulta_fs,
        'exames_todos': exames_qs,
        'exames_pendentes_count': exames_pendentes_qs.count(),
        'consultas_todas': consultas_qs,
        'consultas_pendentes_count': consultas_pendentes_qs.count(),
        'exames_aut_ids_csv': exames_aut_ids_csv,
        'consultas_aut_ids_csv': consultas_aut_ids_csv,
        'exames_aut_count': len(exames_aut_ids),
        'consultas_aut_count': len(consultas_aut_ids),
        'read_only': read_only,
    })


@login_required
@require_access('regulacao')
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
