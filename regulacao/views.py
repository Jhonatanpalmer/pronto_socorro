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
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame, Especialidade, RegulacaoConsulta, Notificacao, PendenciaMensagemExame, PendenciaMensagemConsulta, LocalAtendimento, MedicoAmbulatorio, AgendaMedica, AgendaMedicaDia, AcaoUsuario
from pacientes.models import Paciente
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import (
    UBSForm, MedicoSolicitanteForm, TipoExameForm, RegulacaoExameForm,
    RegulacaoExameCreateForm, EspecialidadeForm, RegulacaoConsultaForm,
    RegulacaoExameBatchForm, RegulacaoConsultaBatchForm, SIGTAPImportForm,
    LocalAtendimentoForm, MedicoAmbulatorioForm, AgendaMedicaForm, AgendaMedicaDiaForm, AgendaMensalGerarForm,
    RegulacaoExameTextosForm, RegulacaoConsultaTextosForm,
)
import os
import shutil
import tempfile
from functools import wraps


@login_required
@require_access('regulacao')
def o_que_fiz_hoje(request):
    """Página que mostra as estatísticas das ações realizadas pelo usuário no dia atual."""
    hoje = timezone.localdate()
    
    # EXAMES - Listas com pacientes
    exames_autorizados_list = RegulacaoExame.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='autorizado'
    ).select_related('paciente', 'tipo_exame')
    
    exames_negados_list = RegulacaoExame.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='negado'
    ).select_related('paciente', 'tipo_exame')
    
    exames_pendenciados_list = RegulacaoExame.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='pendente'
    ).select_related('paciente', 'tipo_exame')
    
    # CONSULTAS - Listas com pacientes
    consultas_autorizadas_list = RegulacaoConsulta.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='autorizado'
    ).select_related('paciente', 'especialidade', 'medico_atendente')
    
    consultas_negadas_list = RegulacaoConsulta.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='negado'
    ).select_related('paciente', 'especialidade', 'medico_atendente')
    
    consultas_pendenciadas_list = RegulacaoConsulta.objects.filter(
        regulador=request.user,
        data_regulacao__date=hoje,
        status='pendente'
    ).select_related('paciente', 'especialidade', 'medico_atendente')
    
    # Contadores para compatibilidade
    exames_autorizados = exames_autorizados_list.count()
    exames_negados = exames_negados_list.count()
    exames_pendenciados = exames_pendenciados_list.count()
    consultas_autorizadas = consultas_autorizadas_list.count()
    consultas_negadas = consultas_negadas_list.count()
    consultas_pendenciadas = consultas_pendenciadas_list.count()
    
    context = {
        'hoje': hoje,
        'exames_autorizados': exames_autorizados,
        'exames_negados': exames_negados,
        'exames_pendenciados': exames_pendenciados,
        'consultas_autorizadas': consultas_autorizadas,
        'consultas_negadas': consultas_negadas,
        'consultas_pendenciadas': consultas_pendenciadas,
        'total_exames': exames_autorizados + exames_negados + exames_pendenciados,
        'total_consultas': consultas_autorizadas + consultas_negadas + consultas_pendenciadas,
        # Listas de pacientes
        'exames_autorizados_list': exames_autorizados_list,
        'exames_negados_list': exames_negados_list,
        'exames_pendenciados_list': exames_pendenciados_list,
        'consultas_autorizadas_list': consultas_autorizadas_list,
        'consultas_negadas_list': consultas_negadas_list,
        'consultas_pendenciadas_list': consultas_pendenciadas_list,
    }
    
    return render(request, 'regulacao/o_que_fiz_hoje.html', context)


@login_required
@require_access('regulacao')
def impressao_consulta(request, pk: int):
    """Página de impressão para uma consulta específica.
    Mostra dados do paciente, UBS solicitante, especialidade, local/data/hora, médico atendente (se houver)
    e informações de autorização (quem autorizou e quando).
    """
    reg = get_object_or_404(
        RegulacaoConsulta.objects.select_related(
            'paciente', 'especialidade', 'ubs_solicitante', 'medico_atendente', 'regulador'
        ),
        pk=pk,
    )
    return render(request, 'regulacao/impressao_consulta.html', {
        'reg': reg,
        'paciente': reg.paciente,
    })


@login_required
@require_access('regulacao')
def impressao_exames_dia(request, paciente_id: int, dia: str):
    """Página de impressão para exames de um paciente em uma data específica.
    Se houver mais de um exame no dia, imprimir todos no mesmo recibo.
    Inclui dados do paciente, UBS solicitante, lista de exames, local/data/hora e dados do autorizador.
    """
    from django.utils.dateparse import parse_date
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    data = parse_date(dia)
    if not data:
        # fallback: tentar formatos comuns
        try:
            from datetime import datetime
            data = datetime.strptime(dia, '%Y-%m-%d').date()
        except Exception:
            data = None

    exames_qs = RegulacaoExame.objects.select_related(
        'paciente', 'tipo_exame', 'ubs_solicitante', 'medico_atendente', 'regulador'
    ).filter(paciente_id=paciente.id, status='autorizado')
    if data:
        exames_qs = exames_qs.filter(data_agendada=data)
    exames = list(exames_qs.order_by('hora_agendada', 'id'))
    
    # Buscar informações dos locais de atendimento para enriquecer os dados
    locais_atendimento = {}
    for local in LocalAtendimento.objects.filter(ativo=True):
        locais_atendimento[local.nome.lower()] = local
    
    # Enriquecer exames com informações do local de atendimento
    for exame in exames:
        exame.local_atendimento_obj = None
        if exame.local_realizacao:
            # Tentar encontrar o local de atendimento correspondente
            local_key = exame.local_realizacao.lower()
            if local_key in locais_atendimento:
                exame.local_atendimento_obj = locais_atendimento[local_key]
            else:
                # Busca parcial por nome similar
                for nome, local_obj in locais_atendimento.items():
                    if nome in local_key or local_key in nome:
                        exame.local_atendimento_obj = local_obj
                        break
    
    return render(request, 'regulacao/impressao_exames_dia.html', {
        'paciente': paciente,
        'data': data,
        'exames': exames,
    })


@login_required
@require_access('regulacao')
def impressao_consultas_dia(request, paciente_id: int, dia: str):
    """Página de impressão para consultas de um paciente em uma data específica.
    Lista todas as consultas autorizadas do paciente para a data informada.
    """
    from django.utils.dateparse import parse_date
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    data = parse_date(dia)
    if not data:
        try:
            from datetime import datetime
            data = datetime.strptime(dia, '%Y-%m-%d').date()
        except Exception:
            data = None

    consultas_qs = RegulacaoConsulta.objects.select_related(
        'paciente', 'especialidade', 'ubs_solicitante', 'medico_atendente', 'regulador'
    ).filter(paciente_id=paciente.id, status='autorizado')
    if data:
        consultas_qs = consultas_qs.filter(data_agendada=data)
    consultas = list(consultas_qs.order_by('hora_agendada', 'id'))

    return render(request, 'regulacao/impressao_consultas_dia.html', {
        'paciente': paciente,
        'data': data,
        'consultas': consultas,
    })


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


# ============ Pendências: resposta da UBS ============

@login_required
@require_access('regulacao')
def responder_pendencia_exame(request, pk: int):
    """Responder à pendência de um exame (UBS da própria unidade ou Regulador)."""
    ubs_user = getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None)
    # Reguladores também podem responder; UBS somente itens da própria unidade
    if ubs_user:
        obj = get_object_or_404(RegulacaoExame, pk=pk, ubs_solicitante=ubs_user)
    else:
        obj = get_object_or_404(RegulacaoExame, pk=pk)
    if obj.status != 'pendente':
        messages.info(request, 'Este exame não está com pendência no momento.')
        return redirect('regulacao-agenda')
    next_url = (request.GET.get('next') or '').strip() or str(reverse_lazy('regulacao-agenda'))
    # Determinar papel do usuário e de quem estamos aguardando
    is_ubs = bool(getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None))
    # Calcular de quem é a vez com base na última mensagem do histórico
    last_msg = obj.pendencia_mensagens.order_by('criado_em').last()
    if obj.status == 'pendente' and not obj.pendencia_resolvida_em:
        if last_msg:
            aguardando = 'ubs' if last_msg.lado == 'regulacao' else 'regulacao'
        else:
            aguardando = 'ubs'
    else:
        aguardando = None
    can_reply = (aguardando == 'ubs' and is_ubs) or (aguardando == 'regulacao' and not is_ubs)
    _ = can_reply  # referenced in template context below

    if request.method == 'POST':
        resposta = (request.POST.get('pendencia_resposta') or '').strip()
        if not resposta:
            messages.error(request, 'Informe a resposta para a pendência.')
        else:
            # UBS responde: grava campos de resposta e mensagem; Regulação responde: só mensagem
            if is_ubs:
                obj.pendencia_resposta = resposta
                obj.pendencia_respondida_em = timezone.now()
                obj.pendencia_respondida_por = request.user
                obj.save(update_fields=['pendencia_resposta','pendencia_respondida_em','pendencia_respondida_por','atualizado_em'])
            # Registrar mensagem no histórico
            PendenciaMensagemExame.objects.create(
                exame=obj,
                autor=request.user,
                lado='ubs' if is_ubs else 'regulacao',
                tipo='mensagem',
                texto=resposta,
            )
            # Notificar lado oposto (se quem respondeu foi UBS, notificar reguladores; se foi regulador, notificar UBS)
            try:
                ubs_do_item = obj.ubs_solicitante
                # Heurística: se usuário tiver perfil_ubs, é UBS; senão, é regulador
                if is_ubs:
                    # Notificar reguladores: opção simples - todos usuários do grupo 'regulacao'
                    from django.contrib.auth.models import User
                    regs = User.objects.filter(groups__name='regulacao').distinct()
                    for u in regs:
                        Notificacao.objects.create(
                            user=u,
                            texto=f"UBS {ubs_do_item.nome} respondeu pendência do exame de {obj.paciente.nome}.",
                            url=str(reverse_lazy('pendencia-exame-responder', kwargs={'pk': obj.pk})),
                        )
                else:
                    # Notificar usuários da UBS solicitante
                    usuarios = getattr(ubs_do_item, 'usuarios', None)
                    if usuarios is not None:
                        for vinc in usuarios.select_related('user').all():
                            Notificacao.objects.create(
                                user=vinc.user,
                                texto=f"Regulação respondeu pendência do exame de {obj.paciente.nome}.",
                                url=str(reverse_lazy('pendencia-exame-responder', kwargs={'pk': obj.pk})),
                            )
            except Exception:
                pass
            if is_ubs:
                messages.success(request, 'Resposta registrada.')
            else:
                messages.success(request, 'Resposta registrada.')
            # cair para o render abaixo, permanecendo na página
    mensagens = obj.pendencia_mensagens.all().order_by('criado_em')
    # Recalcular aguardando/can_reply após possível POST
    last_msg = mensagens.last()
    if obj.status == 'pendente' and not obj.pendencia_resolvida_em:
        if last_msg:
            aguardando = 'ubs' if last_msg.lado == 'regulacao' else 'regulacao'
        else:
            aguardando = 'ubs'
    else:
        aguardando = None
    can_reply = (aguardando == 'ubs' and is_ubs) or (aguardando == 'regulacao' and not is_ubs)
    _ = can_reply
    return render(request, 'regulacao/pendencia_responder.html', {
        'obj': obj,
        'tipo': 'exame',
        'back_url': next_url,
        'mensagens': mensagens,
        'is_ubs': is_ubs,
        'aguardando': aguardando,
        'can_reply': can_reply,
    })


@login_required
@require_access('regulacao')
def responder_pendencia_consulta(request, pk: int):
    """Responder à pendência de uma consulta (UBS da própria unidade ou Regulador)."""
    ubs_user = getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None)
    if ubs_user:
        obj = get_object_or_404(RegulacaoConsulta, pk=pk, ubs_solicitante=ubs_user)
    else:
        obj = get_object_or_404(RegulacaoConsulta, pk=pk)
    if obj.status != 'pendente':
        messages.info(request, 'Esta consulta não está com pendência no momento.')
        return redirect('regulacao-agenda')
    next_url = (request.GET.get('next') or '').strip() or str(reverse_lazy('regulacao-agenda'))
    is_ubs = bool(getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None))
    last_msg = obj.pendencia_mensagens.order_by('criado_em').last()
    if obj.status == 'pendente' and not obj.pendencia_resolvida_em:
        if last_msg:
            aguardando = 'ubs' if last_msg.lado == 'regulacao' else 'regulacao'
        else:
            aguardando = 'ubs'
    else:
        aguardando = None
    can_reply = (aguardando == 'ubs' and is_ubs) or (aguardando == 'regulacao' and not is_ubs)
    _ = can_reply

    if request.method == 'POST':
        resposta = (request.POST.get('pendencia_resposta') or '').strip()
        if not resposta:
            messages.error(request, 'Informe a resposta para a pendência.')
        else:
            if is_ubs:
                obj.pendencia_resposta = resposta
                obj.pendencia_respondida_em = timezone.now()
                obj.pendencia_respondida_por = request.user
                obj.save(update_fields=['pendencia_resposta','pendencia_respondida_em','pendencia_respondida_por','atualizado_em'])
            PendenciaMensagemConsulta.objects.create(
                consulta=obj,
                autor=request.user,
                lado='ubs' if is_ubs else 'regulacao',
                tipo='mensagem',
                texto=resposta,
            )
            # Notificações cruzadas
            try:
                ubs_do_item = obj.ubs_solicitante
                if is_ubs:
                    from django.contrib.auth.models import User
                    regs = User.objects.filter(groups__name='regulacao').distinct()
                    for u in regs:
                        Notificacao.objects.create(
                            user=u,
                            texto=f"UBS {ubs_do_item.nome} respondeu pendência da consulta de {obj.paciente.nome}.",
                            url=str(reverse_lazy('pendencia-consulta-responder', kwargs={'pk': obj.pk})),
                        )
                else:
                    usuarios = getattr(ubs_do_item, 'usuarios', None)
                    if usuarios is not None:
                        for vinc in usuarios.select_related('user').all():
                            Notificacao.objects.create(
                                user=vinc.user,
                                texto=f"Regulação respondeu pendência da consulta de {obj.paciente.nome}.",
                                url=str(reverse_lazy('pendencia-consulta-responder', kwargs={'pk': obj.pk})),
                            )
            except Exception:
                pass
            if is_ubs:
                messages.success(request, 'Resposta registrada.')
            else:
                messages.success(request, 'Resposta registrada.')
    mensagens = obj.pendencia_mensagens.all().order_by('criado_em')
    last_msg = mensagens.last()
    if obj.status == 'pendente' and not obj.pendencia_resolvida_em:
        if last_msg:
            aguardando = 'ubs' if last_msg.lado == 'regulacao' else 'regulacao'
        else:
            aguardando = 'ubs'
    else:
        aguardando = None
    can_reply = (aguardando == 'ubs' and is_ubs) or (aguardando == 'regulacao' and not is_ubs)
    _ = can_reply
    return render(request, 'regulacao/pendencia_responder.html', {
        'obj': obj,
        'tipo': 'consulta',
        'back_url': next_url,
        'mensagens': mensagens,
        'is_ubs': is_ubs,
        'aguardando': aguardando,
        'can_reply': can_reply,
    })


# ============ Edição de textos (Obs/Motivo/Pendência) ============

@login_required
@require_access('regulacao')
def editar_textos_exame(request, pk: int):
    """Página dedicada para editar Observações, Motivo (se negar) e Pendência (motivo) de um Exame."""
    obj = get_object_or_404(RegulacaoExame, pk=pk)
    next_url = (request.GET.get('next') or '').strip() or str(reverse_lazy('regulacao-agenda'))
    campo = (request.GET.get('campo') or '').strip().lower()
    if campo not in ('obs', 'motivo', 'pendencia'):
        campo = 'obs'
    if request.method == 'POST':
        form = RegulacaoExameTextosForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informações atualizadas.')
            return redirect(next_url)
        else:
            messages.error(request, 'Corrija os erros para salvar.')
    else:
        form = RegulacaoExameTextosForm(instance=obj)
    return render(request, 'regulacao/textos_editar.html', {
        'obj': obj,
        'tipo': 'exame',
        'form': form,
        'back_url': next_url,
        'campo': campo,
    })


@login_required
@require_access('regulacao')
def editar_textos_consulta(request, pk: int):
    """Página dedicada para editar Observações, Motivo (se negar) e Pendência (motivo) de uma Consulta."""
    obj = get_object_or_404(RegulacaoConsulta, pk=pk)
    next_url = (request.GET.get('next') or '').strip() or str(reverse_lazy('regulacao-agenda'))
    campo = (request.GET.get('campo') or '').strip().lower()
    if campo not in ('obs', 'motivo', 'pendencia'):
        campo = 'obs'
    if request.method == 'POST':
        form = RegulacaoConsultaTextosForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informações atualizadas.')
            return redirect(next_url)
        else:
            messages.error(request, 'Corrija os erros para salvar.')
    else:
        form = RegulacaoConsultaTextosForm(instance=obj)
    return render(request, 'regulacao/textos_editar.html', {
        'obj': obj,
        'tipo': 'consulta',
        'form': form,
        'back_url': next_url,
        'campo': campo,
    })
# ============ Seleção de UBS (Malote) para Reguladores ============

@login_required
@require_access('regulacao')
def selecionar_malote(request):
    """Pergunta ao regulador qual UBS deseja abrir o malote e salva na sessão.

    - GET: lista UBS ativas para seleção
    - POST: recebe ubs_id, valida e salva em session['malote_ubs_id']
    """
    # Usuários UBS não precisam selecionar malote; redirecionar para portal
    ubs_user = getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None)
    if ubs_user:
        return redirect('regulacao-dashboard')

    if request.method == 'POST':
        try:
            ubs_id = int((request.POST.get('ubs_id') or '0').strip())
        except ValueError:
            ubs_id = 0
        ubs = UBS.objects.filter(ativa=True, id=ubs_id).first()
        if not ubs:
            messages.error(request, 'Selecione uma UBS válida para abrir o malote.')
        else:
            request.session['malote_ubs_id'] = ubs.id
            messages.success(request, f"Malote aberto: {ubs.nome}")
            return redirect('regulacao-dashboard')

    ubs_list = UBS.objects.filter(ativa=True).order_by('nome')
    return render(request, 'regulacao/malote_select.html', {
        'ubs_list': ubs_list,
        'current_malote_id': request.session.get('malote_ubs_id'),
    })



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


# ============ VIEWS PARA MÉDICOS DO AMBULATÓRIO ============

class MedicoAmbulatorioListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoAmbulatorio
    template_name = 'regulacao/medicoambulatorio_list.html'
    context_object_name = 'medico_list'
    ordering = ['nome']


class MedicoAmbulatorioCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoAmbulatorio
    form_class = MedicoAmbulatorioForm
    template_name = 'regulacao/medicoambulatorio_form.html'
    success_url = reverse_lazy('ambulatorio-medico-list')

    def form_valid(self, form):
        messages.success(self.request, 'Médico do ambulatório cadastrado com sucesso!')
        return super().form_valid(form)


class MedicoAmbulatorioUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoAmbulatorio
    form_class = MedicoAmbulatorioForm
    template_name = 'regulacao/medicoambulatorio_form.html'
    success_url = reverse_lazy('ambulatorio-medico-list')

    def form_valid(self, form):
        messages.success(self.request, 'Médico do ambulatório atualizado com sucesso!')
        return super().form_valid(form)


class MedicoAmbulatorioDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = MedicoAmbulatorio
    template_name = 'regulacao/medicoambulatorio_confirm_delete.html'
    success_url = reverse_lazy('ambulatorio-medico-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Médico do ambulatório excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# ============ VIEWS PARA AGENDA MÉDICA ============

class AgendaMedicaListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedica
    template_name = 'regulacao/agendamedica_list.html'
    context_object_name = 'agenda_list'
    ordering = ['medico__nome', 'especialidade__nome', 'dia_semana']

    def get_queryset(self):
        qs = super().get_queryset().select_related('medico', 'especialidade')
        espec = (self.request.GET.get('especialidade') or '').strip()
        medico = (self.request.GET.get('medico') or '').strip()
        if espec.isdigit():
            qs = qs.filter(especialidade_id=int(espec))
        if medico.isdigit():
            qs = qs.filter(medico_id=int(medico))
        return qs


class AgendaMedicaCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedica
    form_class = AgendaMedicaForm
    template_name = 'regulacao/agendamedica_form.html'
    success_url = reverse_lazy('agendamedica-list')

    def form_valid(self, form):
        messages.success(self.request, 'Agenda cadastrada com sucesso!')
        return super().form_valid(form)


class AgendaMedicaUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedica
    form_class = AgendaMedicaForm
    template_name = 'regulacao/agendamedica_form.html'
    success_url = reverse_lazy('agendamedica-list')

    def form_valid(self, form):
        messages.success(self.request, 'Agenda atualizada com sucesso!')
        return super().form_valid(form)


class AgendaMedicaDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedica
    template_name = 'regulacao/agendamedica_confirm_delete.html'
    success_url = reverse_lazy('agendamedica-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Agenda excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
@require_access('regulacao')
def agenda_info(request):
    """Endpoint JSON: retorna dias permitidos (0-6) e capacidades por dia
    para um médico e especialidade informados via GET (?medico=ID&especialidade=ID).
    Também informa, para uma data específica (?data=YYYY-MM-DD), quantas vagas restam.
    """
    from django.utils.dateparse import parse_date
    try:
        med_id = int(request.GET.get('medico') or 0)
        esp_id = int(request.GET.get('especialidade') or 0)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Parâmetros inválidos.'}, status=400)
    if not med_id or not esp_id:
        return JsonResponse({'ok': False, 'error': 'Informe médico e especialidade.'}, status=400)
    # PRIMÁRIO: agenda mensal (por dia)
    from datetime import timedelta
    hoje = timezone.localdate()
    ate = hoje + timedelta(days=210)  # ~7 meses
    per_dia = list(AgendaMedicaDia.objects.filter(
        medico_id=med_id, especialidade_id=esp_id, ativo=True, data__gte=hoje, data__lte=ate
    ).order_by('data'))
    # Fallback: se não houver registros para este esp_id, tentar especialidades com o mesmo nome (case-insensitive)
    if not per_dia:
        try:
            esp = Especialidade.objects.filter(pk=esp_id).first()
            if esp is not None:
                # Match por nome ignorando caixa e espaços
                same_name_ids = list(Especialidade.objects.filter(nome__iexact=esp.nome.strip()).values_list('id', flat=True))
                if same_name_ids:
                    per_dia = list(AgendaMedicaDia.objects.filter(
                        medico_id=med_id, especialidade_id__in=same_name_ids, ativo=True, data__gte=hoje, data__lte=ate
                    ).order_by('data'))
                # Fallback adicional: normalizar em Python e filtrar por nome
                if not per_dia:
                    name_norm = (esp.nome or '').strip().casefold()
                    cand = AgendaMedicaDia.objects.select_related('especialidade').filter(
                        medico_id=med_id, ativo=True, data__gte=hoje, data__lte=ate
                    ).order_by('data')
                    per_dia = [x for x in cand if (getattr(x.especialidade, 'nome', '') or '').strip().casefold() == name_norm]
        except Exception:
            pass
    # Dicionário: data ISO -> capacidade total do dia
    cap_por_data = {x.data.isoformat(): int(x.capacidade or 0) for x in per_dia}
    # Usados por data
    usados_por_data = {
        d_iso: RegulacaoConsulta.objects.filter(medico_atendente_id=med_id, data_agendada=d_iso, status='autorizado').count()
        for d_iso in cap_por_data.keys()
    }
    restantes_por_data = {d_iso: max(0, cap_por_data[d_iso] - usados_por_data.get(d_iso, 0)) for d_iso in cap_por_data.keys()}
    # datas_agenda: todas as datas com agenda cadastrada (independente de vagas)
    datas_agenda = sorted(cap_por_data.keys())
    # datas_disponiveis: somente datas com vagas > 0
    datas_disponiveis = [d for d in datas_agenda if restantes_por_data.get(d, 0) > 0]
    proxima_data_sugerida = datas_disponiveis[0] if datas_disponiveis else None
    # Compat: dias/caps semanais vazios (não usados quando mensal é primário)
    dias = []
    caps = {}
    data_str = (request.GET.get('data') or '').strip()
    restantes = None
    fonte = 'semanal'
    if data_str:
        d = parse_date(data_str)
        if d:
            usados = RegulacaoConsulta.objects.filter(medico_atendente_id=med_id, data_agendada=d, status='autorizado').count()
            cap = cap_por_data.get(d.isoformat())
            if cap is not None:
                restantes = max(0, int(cap) - int(usados))
                fonte = 'dia'
    return JsonResponse({
        'ok': True,
        'dias': dias,
        'capacidades': caps,
        'vagas_restantes': restantes,
        'fonte': fonte,
        'proxima_data_sugerida': proxima_data_sugerida,
        'datas_disponiveis': datas_disponiveis,
        'datas_agenda': datas_agenda,
    })


# ============ Agenda por Data (CRUD + Gerador Mensal) ============

class AgendaMedicaDiaListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedicaDia
    template_name = 'regulacao/agendamedicadia_list.html'
    context_object_name = 'agenda_list'
    ordering = ['data', 'medico__nome']

    def get_queryset(self):
        qs = super().get_queryset().select_related('medico', 'especialidade')
        med = (self.request.GET.get('medico') or '').strip()
        esp = (self.request.GET.get('especialidade') or '').strip()
        di = (self.request.GET.get('di') or '').strip()
        df = (self.request.GET.get('df') or '').strip()
        from django.utils.dateparse import parse_date
        if med.isdigit():
            qs = qs.filter(medico_id=int(med))
        if esp.isdigit():
            qs = qs.filter(especialidade_id=int(esp))
        if di:
            d = parse_date(di)
            if d:
                qs = qs.filter(data__gte=d)
        if df:
            d = parse_date(df)
            if d:
                qs = qs.filter(data__lte=d)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medicos'] = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        return context

    def post(self, request, *args, **kwargs):
        action = (request.POST.get('action') or '').strip()
        ids = request.POST.getlist('ids')
        if action == 'bulk_delete' and ids:
            try:
                ids_int = [int(x) for x in ids]
                deleted, _ = AgendaMedicaDia.objects.filter(id__in=ids_int).delete()
                messages.success(request, f"{deleted} item(ns) excluído(s).")
            except Exception as e:
                messages.error(request, f"Erro ao excluir: {e}")
        else:
            messages.info(request, 'Selecione itens e clique em Excluir selecionados.')
        # Redirecionar mantendo filtros atuais
        return redirect(f"{reverse_lazy('agendadia-list')}?{request.META.get('QUERY_STRING','')}")


class AgendaMedicaDiaCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedicaDia
    form_class = AgendaMedicaDiaForm
    template_name = 'regulacao/agendamedicadia_form.html'
    success_url = reverse_lazy('agendadia-list')

    def form_valid(self, form):
        messages.success(self.request, 'Agenda (por dia) cadastrada com sucesso!')
        return super().form_valid(form)


class AgendaMedicaDiaUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedicaDia
    form_class = AgendaMedicaDiaForm
    template_name = 'regulacao/agendamedicadia_form.html'
    success_url = reverse_lazy('agendadia-list')

    def form_valid(self, form):
        messages.success(self.request, 'Agenda (por dia) atualizada com sucesso!')
        return super().form_valid(form)


class AgendaMedicaDiaDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = AgendaMedicaDia
    template_name = 'regulacao/agendamedicadia_confirm_delete.html'
    success_url = reverse_lazy('agendadia-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Agenda (por dia) excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


@login_required
@require_access('regulacao')
def agenda_mensal_gerar(request):
    form = AgendaMensalGerarForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        med = form.cleaned_data['medico']
        esp = form.cleaned_data['especialidade']
        inicio = form.cleaned_data['inicio']
        meses = form.cleaned_data['meses']
        dias_semana = sorted(int(x) for x in form.cleaned_data['dias_semana'])
        capacidade = form.cleaned_data['capacidade']
        sobrescrever = form.cleaned_data['sobrescrever']

        from datetime import timedelta
        try:
            from dateutil.relativedelta import relativedelta
        except Exception:
            # Fallback simples caso python-dateutil não esteja disponível: aproximar por 30 dias/mes
            class relativedelta:
                def __init__(self, months=0):
                    self.days = months * 30
                def __radd__(self, other):
                    from datetime import timedelta as _td
                    return other + _td(days=self.days)
        created = 0
        updated = 0
        fim = inicio + relativedelta(months=meses)
        d = inicio
        while d < fim:
            if d.weekday() in dias_semana:
                obj, is_created = AgendaMedicaDia.objects.get_or_create(
                    medico=med, especialidade=esp, data=d,
                    defaults={'capacidade': capacidade, 'ativo': True}
                )
                if is_created:
                    created += 1
                elif sobrescrever:
                    if obj.capacidade != capacidade or not obj.ativo:
                        obj.capacidade = capacidade
                        obj.ativo = True
                        obj.save(update_fields=['capacidade','ativo','atualizado_em'])
                        updated += 1
            d += timedelta(days=1)
        messages.success(request, f'Agenda gerada. Criados: {created}, Atualizados: {updated}.')
        return redirect('agendadia-list')
    return render(request, 'regulacao/agendames_gerar.html', { 'form': form })
# ============ VIEWS PARA LOCAIS DE ATENDIMENTO ============

class LocalAtendimentoListView(AccessRequiredMixin, LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = LocalAtendimento
    template_name = 'regulacao/localatendimento_list.html'
    context_object_name = 'locais_list'
    ordering = ['nome']


class LocalAtendimentoCreateView(AccessRequiredMixin, LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = LocalAtendimento
    form_class = LocalAtendimentoForm
    template_name = 'regulacao/localatendimento_form.html'
    success_url = reverse_lazy('localatendimento-list')

    def form_valid(self, form):
        messages.success(self.request, 'Local de atendimento cadastrado com sucesso!')
        return super().form_valid(form)


class LocalAtendimentoUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = LocalAtendimento
    form_class = LocalAtendimentoForm
    template_name = 'regulacao/localatendimento_form.html'
    success_url = reverse_lazy('localatendimento-list')

    def form_valid(self, form):
        messages.success(self.request, 'Local de atendimento atualizado com sucesso!')
        return super().form_valid(form)


class LocalAtendimentoDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'regulacao'
    model = LocalAtendimento
    template_name = 'regulacao/localatendimento_confirm_delete.html'
    success_url = reverse_lazy('localatendimento-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Local de atendimento excluído com sucesso!')
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
        ativo = (self.request.GET.get('ativo') or '').strip()
        if ativo == '1':
            qs = qs.filter(ativo=True)
        elif ativo == '0':
            qs = qs.filter(ativo=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = (self.request.GET.get('q') or '').strip()
        context['ativo_filter'] = (self.request.GET.get('ativo') or '').strip()
        return context

    def post(self, request, *args, **kwargs):
        action = (request.POST.get('action') or '').strip()
        ids = request.POST.getlist('ids')
        if not action or not ids:
            messages.info(request, 'Selecione pelo menos um item e uma ação.')
        else:
            try:
                ids_int = [int(x) for x in ids]
                qs = TipoExame.objects.filter(id__in=ids_int)
                if action == 'ativar':
                    updated = qs.update(ativo=True)
                    messages.success(request, f"{updated} tipo(s) ativado(s).")
                elif action == 'desativar':
                    updated = qs.update(ativo=False)
                    messages.success(request, f"{updated} tipo(s) desativado(s).")
                else:
                    messages.warning(request, 'Ação inválida.')
            except Exception as e:
                messages.error(request, f'Falha ao aplicar ação em massa: {e}')
        # preservar filtros e paginação
        q = (request.POST.get('q') or '').strip()
        ativo = (request.POST.get('ativo') or '').strip()
        page = (request.POST.get('page') or '').strip()
        params = []
        if q:
            params.append(('q', q))
        if ativo in ('0','1'):
            params.append(('ativo', ativo))
        if page:
            params.append(('page', page))
        if params:
            from urllib.parse import urlencode
            return redirect(f"{reverse_lazy('tipo-exame-list')}?{urlencode(params)}")
        return redirect('tipo-exame-list')


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


@login_required
@require_access('regulacao')
def tipo_exame_toggle_ativo(request, pk: int):
    """Alterna rapidamente o status 'ativo' de um TipoExame e volta para a lista mantendo a busca/página."""
    obj = get_object_or_404(TipoExame, pk=pk)
    obj.ativo = not obj.ativo
    obj.save(update_fields=['ativo', 'atualizado_em'])
    messages.success(request, f"Tipo de exame '{obj.nome}' foi {'ativado' if obj.ativo else 'desativado'}.")
    # Preservar parâmetros de query (q, page)
    next_url = request.GET.get('next') or ''
    if next_url:
        try:
            from django.utils.http import url_has_allowed_host_and_scheme
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
        except Exception:
            pass
    # fallback
    return redirect('tipo-exame-list')


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
        # Se usuário for UBS, esta listagem pública não deve ser acessível
        ubs_user = getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            return RegulacaoExame.objects.none()

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

    def dispatch(self, request, *args, **kwargs):
        # Bloquear acesso de UBS a esta listagem e redirecionar ao portal
        if getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None):
            messages.info(request, 'Acesso restrito. Use o Portal da UBS para suas ações.')
            return redirect('regulacao-dashboard')
        return super().dispatch(request, *args, **kwargs)


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
        # Redireciona de acordo com o perfil: UBS volta ao portal; reguladores à listagem
        if getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None):
            return redirect('regulacao-dashboard')
        return redirect('regulacao-list')
    
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

    def get_success_url(self):
        # Fallback, não usado aqui
        return str(reverse_lazy('regulacao-list'))


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

    def get_success_url(self):
        # UBS não navega por listagem pública
        if getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None):
            return str(reverse_lazy('regulacao-dashboard'))
        return str(reverse_lazy('regulacao-list'))


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
        # Pendências da própria UBS (com últimas respostas da Regulação pré-carregadas)
        pend_ex_qs = (
            RegulacaoExame.objects
            .select_related('paciente','tipo_exame')
            .filter(ubs_solicitante=ubs_user, status='pendente')
            .prefetch_related(
                Prefetch(
                    'pendencia_mensagens',
                    queryset=PendenciaMensagemExame.objects.filter(lado='regulacao').order_by('-criado_em'),
                    to_attr='msgs_reg'
                )
            )
            .order_by('-data_solicitacao')
        )
        pend_co_qs = (
            RegulacaoConsulta.objects
            .select_related('paciente','especialidade')
            .filter(ubs_solicitante=ubs_user, status='pendente')
            .prefetch_related(
                Prefetch(
                    'pendencia_mensagens',
                    queryset=PendenciaMensagemConsulta.objects.filter(lado='regulacao').order_by('-criado_em'),
                    to_attr='msgs_reg'
                )
            )
            .order_by('-data_solicitacao')
        )
        notif_nao_lidas = Notificacao.objects.filter(user=request.user, lida=False).order_by('-criado_em')[:10]
        return render(request, 'regulacao/portal_ubs.html', {
            'ubs_atual': ubs_user,
            'pend_ex_count': pend_ex_qs.count(),
            'pend_co_count': pend_co_qs.count(),
            'pend_ex_list': list(pend_ex_qs[:8]),
            'pend_co_list': list(pend_co_qs[:8]),
            'notificacoes': notif_nao_lidas,
        })

    # Reguladores (não UBS): exigir seleção de malote (UBS) e filtrar contagens por essa UBS
    malote_ubs_id = request.session.get('malote_ubs_id')
    ubs_malote = None
    if not malote_ubs_id:
        # Solicitar seleção de UBS (malote)
        return redirect('regulacao-selecionar-malote')
    try:
        ubs_malote = UBS.objects.get(pk=int(malote_ubs_id))
    except Exception:
        # ID inválido na sessão: limpar e exigir nova seleção
        request.session.pop('malote_ubs_id', None)
        return redirect('regulacao-selecionar-malote')

    # Quantidade de pacientes distintos na fila (exames e consultas) para a UBS selecionada
    exames_fila_pacientes = (
        RegulacaoExame.objects
        .filter(status='fila', ubs_solicitante=ubs_malote)
        .values_list('paciente_id', flat=True)
        .distinct()
    )
    consultas_fila_pacientes = (
        RegulacaoConsulta.objects
        .filter(status='fila', ubs_solicitante=ubs_malote)
        .values_list('paciente_id', flat=True)
        .distinct()
    )
    pacientes_fila_exames_count = exames_fila_pacientes.count()
    pacientes_fila_consultas_count = consultas_fila_pacientes.count()

    # Pendências da UBS do malote
    pend_ex_qs = (
        RegulacaoExame.objects
        .select_related('paciente','tipo_exame')
        .filter(ubs_solicitante=ubs_malote, status='pendente')
        .prefetch_related(
            Prefetch(
                'pendencia_mensagens',
                queryset=PendenciaMensagemExame.objects.filter(lado='regulacao').order_by('-criado_em'),
                to_attr='msgs_reg'
            ),
            Prefetch(
                'pendencia_mensagens',
                queryset=PendenciaMensagemExame.objects.filter(lado='ubs').order_by('-criado_em'),
                to_attr='msgs_ubs'
            )
        )
        .order_by('-data_solicitacao')
    )
    pend_co_qs = (
        RegulacaoConsulta.objects
        .select_related('paciente','especialidade')
        .filter(ubs_solicitante=ubs_malote, status='pendente')
        .prefetch_related(
            Prefetch(
                'pendencia_mensagens',
                queryset=PendenciaMensagemConsulta.objects.filter(lado='regulacao').order_by('-criado_em'),
                to_attr='msgs_reg'
            ),
            Prefetch(
                'pendencia_mensagens',
                queryset=PendenciaMensagemConsulta.objects.filter(lado='ubs').order_by('-criado_em'),
                to_attr='msgs_ubs'
            )
        )
        .order_by('-data_solicitacao')
    )

    notif_nao_lidas = Notificacao.objects.filter(user=request.user, lida=False).order_by('-criado_em')[:10]
    return render(request, 'regulacao/dashboard.html', {
        'pacientes_fila_exames_count': pacientes_fila_exames_count,
        'pacientes_fila_consultas_count': pacientes_fila_consultas_count,
        'ubs_malote': ubs_malote,
        'pend_ex_count': pend_ex_qs.count(),
        'pend_co_count': pend_co_qs.count(),
        'pend_ex_list': list(pend_ex_qs[:8]),
        'pend_co_list': list(pend_co_qs[:8]),
        'notificacoes': notif_nao_lidas,
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
        # Se usuário for UBS, impedir acesso a esta página pública e redirecionar no dispatch
        ubs_user = getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            qs = qs.none()
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
        context['hoje'] = timezone.localdate()
        return context

    def dispatch(self, request, *args, **kwargs):
        # Bloquear acesso de UBS a esta listagem e redirecionar ao portal
        if getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None):
            messages.info(request, 'Acesso restrito. Use o Portal da UBS para suas ações.')
            return redirect('regulacao-dashboard')
        return super().dispatch(request, *args, **kwargs)


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

    def dispatch(self, request, *args, **kwargs):
        # Após criar, UBS não deve navegar por listagens; manter criação permitida.
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # UBS retorna ao portal; regulador permanece nas listagens
        if getattr(getattr(self.request.user, 'perfil_ubs', None), 'ubs', None):
            return str(reverse_lazy('regulacao-dashboard'))
        return str(reverse_lazy('consulta-list'))


# ============ Notificações ============

@login_required
@require_access('regulacao')
def minhas_notificacoes(request):
    """Lista as notificações do usuário autenticado com opção de marcar como lidas."""
    qs = Notificacao.objects.filter(user=request.user).order_by('-criado_em')
    page = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page)
    # Contagem de não lidas para badge
    nao_lidas = Notificacao.objects.filter(user=request.user, lida=False).count()
    return render(request, 'regulacao/notificacoes.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'nao_lidas_count': nao_lidas,
    })


@login_required
@require_access('regulacao')
def notificacao_marcar_lida(request, pk: int):
    notif = get_object_or_404(Notificacao, pk=pk, user=request.user)
    if not notif.lida:
        notif.lida = True
        notif.save(update_fields=['lida'])
        messages.success(request, 'Notificação marcada como lida.')
    next_url = request.GET.get('next') or reverse_lazy('notificacoes-list')
    return redirect(next_url)

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

    # Detalhes por item (especialidade, UBS, status e, quando aplicável, data/hora)
    detalhes = []
    for r in base_qs.order_by('data_solicitacao'):
        espec_nome = r.especialidade.nome if r.especialidade else '-'
        ubs_nome = r.ubs_solicitante.nome if r.ubs_solicitante else '-'
        ag_txt = ''
        # Adicionar data de solicitação quando estiver em fila de espera
        if r.status == 'fila' and r.data_solicitacao:
            try:
                ag_txt = f" (solicitado em {r.data_solicitacao.strftime('%d/%m/%Y')})"
            except Exception:
                pass
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
        # Data de solicitação para itens em fila de espera
        if r.status == 'fila' and r.data_solicitacao:
            try:
                ag_txt = f" (solicitado em {r.data_solicitacao.strftime('%d/%m/%Y')})"
            except Exception:
                pass
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
    # Se regulador tiver malote selecionado, restringir à UBS escolhida
    malote_ubs_id = request.session.get('malote_ubs_id')
    if malote_ubs_id:
        try:
            exames_qs = exames_qs.filter(ubs_solicitante_id=int(malote_ubs_id))
        except Exception:
            pass
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
    if malote_ubs_id:
        try:
            consultas_qs = consultas_qs.filter(ubs_solicitante_id=int(malote_ubs_id))
        except Exception:
            pass
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

    # Ordenar por mais antigos primeiro (campo 'desde'), com desempate por nome do paciente
    exames_grouped = sorted(
        grupos_ex.values(), key=lambda x: (x['desde'], (x['paciente'].nome or '').lower())
    )

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

    # Ordenar por mais antigos primeiro também para consultas
    consultas_grouped = sorted(
        grupos_co.values(), key=lambda x: (x['desde'], (x['paciente'].nome or '').lower())
    )

    # Paginação independente
    # Paginação: no máximo 10 itens por página (valor padrão 10)
    try:
        per_page_ex = int(request.GET.get('per_ex', 10) or 10)
    except (TypeError, ValueError):
        per_page_ex = 10
    try:
        per_page_co = int(request.GET.get('per_co', 10) or 10)
    except (TypeError, ValueError):
        per_page_co = 10
    # Garantir limites (1..10)
    if per_page_ex < 1:
        per_page_ex = 10
    if per_page_co < 1:
        per_page_co = 10
    if per_page_ex > 10:
        per_page_ex = 10
    if per_page_co > 10:
        per_page_co = 10

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
    # timezone já importado no topo do arquivo
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

#### Impressão removida: rotas e templates de comprovantes excluídos


# ============ Resultado de Atendimento (Compareceu/Faltou) ============

@login_required
@require_access('regulacao')
def registrar_resultado_exame(request, pk: int):
    if request.method != 'POST':
        return redirect('regulacao-agenda')
    # UBS não pode registrar resultado de atendimento
    if is_ubs_user(request.user):
        messages.error(request, 'Usuários das UBS não podem alterar o resultado do atendimento (aguardando/compareceu/faltou).')
        return redirect(_back_to_agenda(request, default_only='ex', default_hash='#exames-pane'))
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
    # UBS não pode registrar resultado de atendimento
    if is_ubs_user(request.user):
        messages.error(request, 'Usuários das UBS não podem alterar o resultado do atendimento (aguardando/compareceu/faltou).')
        return redirect(_back_to_agenda(request, default_only='co', default_hash='#consultas-pane'))
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
    """Monta uma URL de retorno à agenda preservando filtros essenciais (di/df/only) e aba.

    Observação: coleta parâmetros tanto do GET quanto do POST, mas restringe a uma whitelist
    para evitar vazar campos do formulário (como csrf, resultado, observacao).
    """
    base = '/regulacao/agenda/'
    from django.utils.http import urlencode
    allowed = {'di', 'df', 'only'}
    params = []

    def add_allowed(source):
        for k in source.keys():
            if k in allowed:
                for v in source.getlist(k):
                    params.append((k, v))

    # Preservar do GET (URL atual) e do POST (inputs ocultos)
    add_allowed(request.GET)
    add_allowed(request.POST)

    # Se não há "only" e foi fornecido um default, usar
    if default_only and not any(k == 'only' for k, _ in params):
        params.append(('only', default_only))
    qs = urlencode(params)
    if qs:
        return f"{base}?{qs}{default_hash}"
    return f"{base}{default_hash}"


@login_required
@require_access('regulacao')
def registrar_resultados_agenda(request):
    """Recebe POST em massa da agenda e atualiza resultados de múltiplas consultas/exames.

    Campos esperados (se existirem):
      - di/df/only (preservar filtros)
      - co-<id>-resultado, co-<id>-observacao
      - ex-<id>-resultado, ex-<id>-observacao
    """
    if request.method != 'POST':
        return redirect('regulacao-agenda')

    # UBS não pode registrar resultado de atendimento em lote
    if is_ubs_user(request.user):
        messages.error(request, 'Usuários das UBS não podem alterar o resultado do atendimento (aguardando/compareceu/faltou).')
        # Tentar voltar para a aba correspondente
        only_tab = (request.POST.get('only') or '').strip()
        default_only = only_tab if only_tab in ('co', 'ex') else None
        default_hash = '#consultas-pane' if default_only == 'co' else ('#exames-pane' if default_only == 'ex' else '')
        return redirect(_back_to_agenda(request, default_only=default_only, default_hash=default_hash))

    hoje = timezone.localdate()
    updated_co = skipped_co = 0
    updated_ex = skipped_ex = 0

    # Coletar IDs informados no POST
    co_ids = set()
    ex_ids = set()
    for key in request.POST.keys():
        if key.startswith('co-') and key.endswith('-resultado'):
            try:
                pk = int(key.split('-')[1])
                co_ids.add(pk)
            except (ValueError, IndexError):
                continue
        elif key.startswith('ex-') and key.endswith('-resultado'):
            try:
                pk = int(key.split('-')[1])
                ex_ids.add(pk)
            except (ValueError, IndexError):
                continue

    # Processar Consultas
    if co_ids:
        regs = {r.id: r for r in RegulacaoConsulta.objects.filter(id__in=co_ids)}
        for pk in co_ids:
            reg = regs.get(pk)
            if not reg:
                continue
            # Apenas autorizadas e com data passada/hoje
            if reg.status != 'autorizado' or not reg.data_agendada or reg.data_agendada > hoje:
                skipped_co += 1
                continue
            val = (request.POST.get(f'co-{pk}-resultado') or '').strip()
            if val not in ('compareceu', 'faltou', 'pendente'):
                skipped_co += 1
                continue
            obs = (request.POST.get(f'co-{pk}-observacao') or '').strip()
            reg.resultado_atendimento = val
            reg.resultado_observacao = obs
            reg.resultado_por = request.user
            reg.resultado_em = timezone.now()
            reg.save(update_fields=['resultado_atendimento','resultado_observacao','resultado_por','resultado_em','atualizado_em'])
            updated_co += 1

    # Processar Exames
    if ex_ids:
        regs = {r.id: r for r in RegulacaoExame.objects.filter(id__in=ex_ids)}
        for pk in ex_ids:
            reg = regs.get(pk)
            if not reg:
                continue
            if reg.status != 'autorizado' or not reg.data_agendada or reg.data_agendada > hoje:
                skipped_ex += 1
                continue
            val = (request.POST.get(f'ex-{pk}-resultado') or '').strip()
            if val not in ('compareceu', 'faltou', 'pendente'):
                skipped_ex += 1
                continue
            obs = (request.POST.get(f'ex-{pk}-observacao') or '').strip()
            reg.resultado_atendimento = val
            reg.resultado_observacao = obs
            reg.resultado_por = request.user
            reg.resultado_em = timezone.now()
            reg.save(update_fields=['resultado_atendimento','resultado_observacao','resultado_por','resultado_em','atualizado_em'])
            updated_ex += 1

    # Mensagens
    if updated_co or updated_ex:
        parts = []
        if updated_co:
            parts.append(f"{updated_co} consulta(s)")
        if updated_ex:
            parts.append(f"{updated_ex} exame(s)")
        messages.success(request, f"Resultados salvos: {', '.join(parts)}.")
    if skipped_co or skipped_ex:
        parts = []
        if skipped_co:
            parts.append(f"{skipped_co} consulta(s) ignoradas (não autorizadas ou data futura)")
        if skipped_ex:
            parts.append(f"{skipped_ex} exame(s) ignorados (não autorizados ou data futura)")
        messages.warning(request, '; '.join(parts))

    # Redireciona de volta preservando filtros e aba
    # Se o POST tiver only, será preservado; senão, usar co como padrão se houve consultas, senão ex
    default_only = 'co' if co_ids else ('ex' if ex_ids else None)
    default_hash = '#consultas-pane' if default_only == 'co' else ('#exames-pane' if default_only == 'ex' else '')
    return redirect(_back_to_agenda(request, default_only=default_only, default_hash=default_hash))

@login_required
@require_access('regulacao')
def paciente_pedido(request, paciente_id):
    """Página única por paciente para listar todas as solicitações e autorizar/agendar seleções."""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    # UBS: somente visualização; não pode autorizar/
    read_only = is_ubs_user(request.user)
    
    # Exames do paciente (todos para contexto; foco em fila/pendente para autorizar)
    exames_qs = RegulacaoExame.objects.select_related(
        'tipo_exame',
        'tipo_exame__especialidade',
        'ubs_solicitante',
        'medico_solicitante',
        'medico_atendente'
    ).filter(paciente=paciente).order_by('-data_solicitacao')
    exames_pendentes_qs = exames_qs.filter(status__in=['fila', 'pendente'])

    # Consultas do paciente
    consultas_qs = RegulacaoConsulta.objects.select_related('especialidade', 'ubs_solicitante', 'medico_solicitante').filter(paciente=paciente).order_by('-data_solicitacao')
    consultas_pendentes_qs = consultas_qs.filter(status__in=['fila', 'pendente'])
    # Filtro opcional: "Aguardando resposta" para Regulação
    # Mostra apenas itens que foram marcados como pendentes e já possuem resposta da UBS
    pend_only = (request.GET.get('pend') == '1')
    if pend_only:
        exames_pendentes_qs = exames_pendentes_qs.filter(status='pendente', pendencia_respondida_em__isnull=False)
        consultas_pendentes_qs = consultas_pendentes_qs.filter(status='pendente', pendencia_respondida_em__isnull=False)
    
    # Para usuários da regulação (não UBS): aplicar filtro por UBS do malote selecionado
    if not read_only:  # Se não for usuário UBS (ou seja, é regulação)
        malote_ubs_id = request.session.get('malote_ubs_id')
        if malote_ubs_id:
            try:
                ubs_malote_id = int(malote_ubs_id)
                # Filtrar para mostrar apenas solicitações da UBS selecionada no malote
                exames_qs = exames_qs.filter(ubs_solicitante_id=ubs_malote_id)
                exames_pendentes_qs = exames_pendentes_qs.filter(ubs_solicitante_id=ubs_malote_id)
                consultas_qs = consultas_qs.filter(ubs_solicitante_id=ubs_malote_id)
                consultas_pendentes_qs = consultas_pendentes_qs.filter(ubs_solicitante_id=ubs_malote_id)
            except (ValueError, TypeError):
                # Se malote_ubs_id não for válido, redirecionar para seleção
                messages.warning(request, 'Selecione uma UBS para abrir o malote antes de visualizar pedidos.')
                return redirect('regulacao-selecionar-malote')

    ExameFormSet = modelformset_factory(RegulacaoExame, form=RegulacaoExameBatchForm, extra=0, can_delete=False)
    ConsultaFormSet = modelformset_factory(RegulacaoConsulta, form=RegulacaoConsultaBatchForm, extra=0, can_delete=False)

    if request.method == 'POST':
        if read_only:
            messages.error(request, 'Usuários de UBS não podem autorizar ou negar solicitações. Acesso somente para visualização.')
            return redirect('paciente-pedido', paciente_id=paciente.id)
        submitted_exames = any(k in request.POST for k in ('submit_exames','deny_exames','pend_exames'))
        submitted_consultas = any(k in request.POST for k in ('submit_consultas','deny_consultas','pend_consultas'))
        exame_fs = ExameFormSet(request.POST if submitted_exames else None, queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(request.POST if submitted_consultas else None, queryset=consultas_pendentes_qs, prefix='co')
        # Anexar request aos forms (para validação contextual)
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            setattr(f, 'request', request)

        # Processar apenas o formset submetido
        if submitted_exames:
            if exame_fs.is_valid():
                aprovados_exames = 0
                negados_exames = 0
                pendenciados_exames = 0
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
                        prev_status = inst.status
                        if form.cleaned_data.get('autorizar'):
                            inst.status = 'autorizado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # Ambos os perfis podem agendar ao autorizar
                            inst.local_realizacao = form.cleaned_data.get('local_realizacao')
                            inst.data_agendada = form.cleaned_data.get('data_agendada')
                            inst.hora_agendada = form.cleaned_data.get('hora_agendada')
                            inst.medico_atendente = form.cleaned_data.get('medico_atendente')
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            aprovados_exames += 1
                            aprovados_ids.append(inst.id)
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='autorizar_exame',
                                exame=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.motivo_decisao or ''
                            )
                            # Notificar UBS quando um item que estava pendente foi autorizado/agendado
                            if prev_status == 'pendente':
                                try:
                                    usuarios = getattr(inst.ubs_solicitante, 'usuarios', None)
                                    if usuarios is not None:
                                        data_txt = inst.data_agendada.strftime('%d/%m/%Y') if inst.data_agendada else None
                                        hora_txt = inst.hora_agendada.strftime('%H:%M') if inst.hora_agendada else None
                                        when_txt = (
                                            f" para {data_txt}{(' às ' + hora_txt) if hora_txt else ''}" if data_txt else ''
                                        )
                                        for vinc in usuarios.select_related('user').all():
                                            Notificacao.objects.create(
                                                user=vinc.user,
                                                texto=(
                                                    f"Exame de {inst.paciente.nome} em pendência foi agendado{when_txt}."
                                                ),
                                                url=str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': inst.paciente_id})) + "?only=ex",
                                            )
                                except Exception:
                                    pass
                        elif form.cleaned_data.get('negar'):
                            inst.status = 'negado'
                            inst.regulador = request.user
                            inst.data_regulacao = timezone.now()
                            # limpar dados de agendamento ao negar
                            inst.local_realizacao = ''
                            inst.data_agendada = None
                            inst.hora_agendada = None
                            inst.medico_atendente = None
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.motivo_decisao = form.cleaned_data.get('motivo_decisao') or ''
                            inst.save()
                            negados_exames += 1
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='negar_exame',
                                exame=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.motivo_decisao or ''
                            )
                        elif form.cleaned_data.get('pendenciar'):
                            # Marcar como pendente e registrar motivo
                            inst.status = 'pendente'
                            inst.pendencia_motivo = form.cleaned_data.get('pendencia_motivo') or ''
                            inst.pendencia_aberta_por = request.user
                            inst.pendencia_aberta_em = timezone.now()
                            # Limpar qualquer resposta anterior, voltando a aguardar a UBS
                            inst.pendencia_resposta = ''
                            inst.pendencia_respondida_em = None
                            inst.pendencia_respondida_por = None
                            # limpar dados de agendamento
                            inst.local_realizacao = ''
                            inst.data_agendada = None
                            inst.hora_agendada = None
                            inst.medico_atendente = None
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.save(update_fields=['status','pendencia_motivo','pendencia_aberta_por','pendencia_aberta_em','pendencia_resposta','pendencia_respondida_em','pendencia_respondida_por','local_realizacao','data_agendada','hora_agendada','medico_atendente','observacoes_regulacao','atualizado_em'])
                            # Registrar abertura no histórico
                            PendenciaMensagemExame.objects.create(
                                exame=inst,
                                autor=request.user,
                                lado='regulacao' if not getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None) else 'ubs',
                                tipo='abertura',
                                texto=inst.pendencia_motivo,
                            )
                            pendenciados_exames += 1
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='pendenciar_exame',
                                exame=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.pendencia_motivo or ''
                            )
                        else:
                            # Caso no futuro exista uma ação explícita de "retornar à fila",
                            # notificar a UBS quando um item que estava pendente voltar para a fila.
                            if prev_status == 'pendente' and inst.status == 'fila':
                                try:
                                    usuarios = getattr(inst.ubs_solicitante, 'usuarios', None)
                                    if usuarios is not None:
                                        for vinc in usuarios.select_related('user').all():
                                            Notificacao.objects.create(
                                                user=vinc.user,
                                                texto=(
                                                    f"Exame de {inst.paciente.nome} em pendência retornou à fila de espera."
                                                ),
                                                url=str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': inst.paciente_id})) + "?only=ex",
                                            )
                                except Exception:
                                    pass
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
                if pendenciados_exames:
                    messages.warning(request, f"{pendenciados_exames} exame(s) marcados como pendentes para retorno da UBS.")
                if not aprovados_exames and not negados_exames and not pendenciados_exames:
                    messages.info(request, 'Nenhum exame marcado para autorização.')
                # Voltar preservando a aba e o filtro de pendências (se ativo)
                only_param = (request.GET.get('only') or 'ex').strip() or 'ex'
                pend_param = '1' if (request.GET.get('pend') == '1') else None
                base_url = str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': paciente.id}))
                if pend_param:
                    return redirect(f"{base_url}?only={only_param}&pend=1")
                else:
                    return redirect(f"{base_url}?only={only_param}")
            else:
                messages.error(request, 'Corrija os erros nos exames para prosseguir.')

        if submitted_consultas:
            if consulta_fs.is_valid():
                aprovados_consultas = 0
                negadas_consultas = 0
                pendenciadas_consultas = 0
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
                        prev_status = inst.status
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
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='autorizar_consulta',
                                consulta=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.motivo_decisao or ''
                            )
                            # Notificar UBS quando um item que estava pendente foi autorizado/agendado
                            if prev_status == 'pendente':
                                try:
                                    usuarios = getattr(inst.ubs_solicitante, 'usuarios', None)
                                    if usuarios is not None:
                                        data_txt = inst.data_agendada.strftime('%d/%m/%Y') if inst.data_agendada else None
                                        hora_txt = inst.hora_agendada.strftime('%H:%M') if inst.hora_agendada else None
                                        when_txt = (
                                            f" para {data_txt}{(' às ' + hora_txt) if hora_txt else ''}" if data_txt else ''
                                        )
                                        for vinc in usuarios.select_related('user').all():
                                            Notificacao.objects.create(
                                                user=vinc.user,
                                                texto=(
                                                    f"Consulta de {inst.paciente.nome} em pendência foi agendada{when_txt}."
                                                ),
                                                url=str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': inst.paciente_id})) + "?only=co",
                                            )
                                except Exception:
                                    pass
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
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='negar_consulta',
                                consulta=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.motivo_decisao or ''
                            )
                        elif form.cleaned_data.get('pendenciar'):
                            inst.status = 'pendente'
                            inst.pendencia_motivo = form.cleaned_data.get('pendencia_motivo') or ''
                            inst.pendencia_aberta_por = request.user
                            inst.pendencia_aberta_em = timezone.now()
                            # Limpar qualquer resposta anterior, voltando a aguardar a UBS
                            inst.pendencia_resposta = ''
                            inst.pendencia_respondida_em = None
                            inst.pendencia_respondida_por = None
                            # limpar dados de agendamento
                            inst.local_atendimento = ''
                            inst.data_agendada = None
                            inst.hora_agendada = None
                            inst.observacoes_regulacao = form.cleaned_data.get('observacoes_regulacao') or ''
                            inst.save(update_fields=['status','pendencia_motivo','pendencia_aberta_por','pendencia_aberta_em','pendencia_resposta','pendencia_respondida_em','pendencia_respondida_por','local_atendimento','data_agendada','hora_agendada','observacoes_regulacao','atualizado_em'])
                            # Registrar abertura no histórico
                            PendenciaMensagemConsulta.objects.create(
                                consulta=inst,
                                autor=request.user,
                                lado='regulacao' if not getattr(getattr(request.user, 'perfil_ubs', None), 'ubs', None) else 'ubs',
                                tipo='abertura',
                                texto=inst.pendencia_motivo,
                            )
                            pendenciadas_consultas += 1
                            # Registrar ação do usuário
                            AcaoUsuario.objects.create(
                                usuario=request.user,
                                tipo_acao='pendenciar_consulta',
                                consulta=inst,
                                paciente_nome=inst.paciente.nome,
                                motivo=inst.pendencia_motivo or ''
                            )
                        else:
                            # Caso no futuro exista uma ação explícita de "retornar à fila",
                            # notificar a UBS quando um item que estava pendente voltar para a fila.
                            if prev_status == 'pendente' and inst.status == 'fila':
                                try:
                                    usuarios = getattr(inst.ubs_solicitante, 'usuarios', None)
                                    if usuarios is not None:
                                        for vinc in usuarios.select_related('user').all():
                                            Notificacao.objects.create(
                                                user=vinc.user,
                                                texto=(
                                                    f"Consulta de {inst.paciente.nome} em pendência retornou à fila de espera."
                                                ),
                                                url=str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': inst.paciente_id})) + "?only=co",
                                            )
                                except Exception:
                                    pass
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
                if pendenciadas_consultas:
                    messages.warning(request, f"{pendenciadas_consultas} consulta(s) marcadas como pendentes para retorno da UBS.")
                if not aprovados_consultas and not negadas_consultas and not pendenciadas_consultas:
                    messages.info(request, 'Nenhuma consulta marcada para autorização.')
                # Voltar preservando a aba e o filtro de pendências (se ativo)
                only_param = (request.GET.get('only') or 'co').strip() or 'co'
                pend_param = '1' if (request.GET.get('pend') == '1') else None
                base_url = str(reverse_lazy('paciente-pedido', kwargs={'paciente_id': paciente.id}))
                if pend_param:
                    return redirect(f"{base_url}?only={only_param}&pend=1")
                else:
                    return redirect(f"{base_url}?only={only_param}")
            else:
                messages.error(request, 'Corrija os erros nas consultas para prosseguir.')
    else:
        exame_fs = ExameFormSet(queryset=exames_pendentes_qs, prefix='ex')
        consulta_fs = ConsultaFormSet(queryset=consultas_pendentes_qs, prefix='co')
        for f in list(exame_fs.forms) + list(consulta_fs.forms):
            setattr(f, 'request', request)
        if 'medico_atendente' in consulta_fs.empty_form.fields:
            consulta_fs.empty_form.fields['medico_atendente'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        for f in consulta_fs.forms:
            if 'medico_atendente' in f.fields:
                # Se a consulta já possui especialidade, filtrar por ela
                espec = getattr(f.instance, 'especialidade', None)
                if espec is not None:
                    f.fields['medico_atendente'].queryset = MedicoAmbulatorio.objects.filter(ativo=True, especialidades=espec).order_by('nome')
                else:
                    f.fields['medico_atendente'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')

    # IDs autorizados (para botões de impressão)
    exames_aut_ids = list(exames_qs.filter(status='autorizado').values_list('id', flat=True))
    consultas_aut_ids = list(consultas_qs.filter(status='autorizado').values_list('id', flat=True))
    exames_aut_ids_csv = ','.join(str(i) for i in exames_aut_ids)
    consultas_aut_ids_csv = ','.join(str(i) for i in consultas_aut_ids)

    # Informação sobre UBS do malote (para usuários da regulação)
    ubs_malote = None
    if not read_only:  # Se for usuário da regulação
        malote_ubs_id = request.session.get('malote_ubs_id')
        if malote_ubs_id:
            try:
                ubs_malote = UBS.objects.get(pk=int(malote_ubs_id))
            except UBS.DoesNotExist:
                pass

    only = (request.GET.get('only') or '').strip()
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
        'ubs_malote': ubs_malote,
        'only': only,
        'pend': pend_only,
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

                    # Não ativar automaticamente durante importação; fica inativo até o usuário ativar
                    obj, is_created = TipoExame.objects.get_or_create(codigo_sus=cod, defaults={
                        'nome': nome,
                        'codigo': cod,
                    })
                    changed = False
                    if not is_created:
                        if obj.nome != nome:
                            obj.nome = nome
                            changed = True
                        if not obj.codigo:
                            obj.codigo = cod
                            changed = True
                        # não alterar automaticamente o status 'ativo'
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

@csrf_exempt
@login_required
@require_access('regulacao')
@require_POST
@require_POST
@login_required
def salvar_acao_ajax(request):
    """View AJAX para salvar ações de pendência e negativa automaticamente."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"AJAX Request recebida - User: {request.user}, Method: {request.method}")
        
        # Verificar se é usuário da regulação
        if is_ubs_user(request.user):
            logger.warning(f"Usuário UBS tentou acessar: {request.user}")
            return JsonResponse({'success': False, 'error': 'Usuários de UBS não podem autorizar ou negar solicitações.'})
        
        # Obter dados do POST
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')  # 'exame' ou 'consulta'
        action = request.POST.get('action')  # 'negar' ou 'pendenciar'
        motivo = request.POST.get('motivo', '').strip()
        
        logger.info(f"Dados recebidos - ID: {item_id}, Type: {item_type}, Action: {action}, Motivo: {motivo[:50]}...")
        
        if not all([item_id, item_type, action, motivo]):
            return JsonResponse({'success': False, 'error': 'Dados incompletos.'})
        
        if action not in ['negar', 'pendenciar']:
            return JsonResponse({'success': False, 'error': 'Ação inválida.'})
        
        if item_type not in ['exame', 'consulta']:
            return JsonResponse({'success': False, 'error': 'Tipo de item inválido.'})
        
        # Processar baseado no tipo
        with transaction.atomic():
            if item_type == 'exame':
                regulacao = get_object_or_404(RegulacaoExame, pk=item_id)
                
                if action == 'negar':
                    regulacao.status = 'negado'
                    regulacao.motivo_decisao = motivo
                    regulacao.data_regulacao = timezone.now()
                    regulacao.regulador = request.user
                    regulacao.save()
                    
                    # Registrar ação do usuário
                    AcaoUsuario.objects.create(
                        usuario=request.user,
                        tipo_acao='negar_exame',
                        exame=regulacao,
                        paciente_nome=regulacao.paciente.nome,
                        motivo=motivo
                    )
                    
                elif action == 'pendenciar':
                    regulacao.status = 'pendente'
                    regulacao.pendencia_motivo = motivo
                    regulacao.pendencia_aberta_em = timezone.now()
                    regulacao.pendencia_aberta_por = request.user
                    regulacao.pendencia_respondida_em = None
                    regulacao.pendencia_resposta = ''
                    regulacao.save()
                    
                    # Registrar ação do usuário
                    AcaoUsuario.objects.create(
                        usuario=request.user,
                        tipo_acao='pendenciar_exame',
                        exame=regulacao,
                        paciente_nome=regulacao.paciente.nome,
                        motivo=motivo
                    )
                    
                    # Registrar mensagem de pendência
                    PendenciaMensagemExame.objects.create(
                        exame=regulacao,
                        autor=request.user,
                        lado='regulacao',
                        tipo='abertura',
                        texto=motivo,
                    )
                    
            elif item_type == 'consulta':
                regulacao = get_object_or_404(RegulacaoConsulta, pk=item_id)
                
                if action == 'negar':
                    regulacao.status = 'negado'
                    regulacao.motivo_decisao = motivo
                    regulacao.data_regulacao = timezone.now()
                    regulacao.regulador = request.user
                    regulacao.save()
                    
                    # Registrar ação do usuário
                    AcaoUsuario.objects.create(
                        usuario=request.user,
                        tipo_acao='negar_consulta',
                        consulta=regulacao,
                        paciente_nome=regulacao.paciente.nome,
                        motivo=motivo
                    )
                    
                elif action == 'pendenciar':
                    regulacao.status = 'pendente'
                    regulacao.pendencia_motivo = motivo
                    regulacao.pendencia_aberta_em = timezone.now()
                    regulacao.pendencia_aberta_por = request.user
                    regulacao.pendencia_respondida_em = None
                    regulacao.pendencia_resposta = ''
                    regulacao.save()
                    
                    # Registrar ação do usuário
                    AcaoUsuario.objects.create(
                        usuario=request.user,
                        tipo_acao='pendenciar_consulta',
                        consulta=regulacao,
                        paciente_nome=regulacao.paciente.nome,
                        motivo=motivo
                    )
                    
                    # Registrar mensagem de pendência
                    PendenciaMensagemConsulta.objects.create(
                        consulta=regulacao,
                        autor=request.user,
                        lado='regulacao',
                        tipo='abertura',
                        texto=motivo,
                    )
        
        return JsonResponse({'success': True, 'message': f'Ação "{action}" salva com sucesso.'})
        
    except Exception as e:
        logger.error(f"Erro na view AJAX: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})
