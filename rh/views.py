import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST

from secretaria_it.access import require_access
from .models import FuncionarioRH, AtestadoMedico
from .forms import FuncionarioRHForm, AtestadoMedicoForm
from rh.cid10_data import get_cid_description


@login_required
@require_access('rh')
def funcionario_list(request):
    qs = FuncionarioRH.objects.all()

    nome = (request.GET.get('nome') or '').strip()
    cpf_raw = (request.GET.get('cpf') or '').strip()
    cpf = re.sub(r'\D', '', cpf_raw)
    cargo = (request.GET.get('cargo') or '').strip()
    situacao = (request.GET.get('situacao') or '').strip()
    vinculo = (request.GET.get('vinculo') or '').strip()
    setor = (request.GET.get('setor') or '').strip()

    if nome:
        qs = qs.filter(nome__icontains=nome)
    if cpf:
        qs = qs.filter(cpf__icontains=cpf)
    if cargo:
        qs = qs.filter(cargo__icontains=cargo)

    situacoes_validas = {choice.value for choice in FuncionarioRH.Situacao}
    if situacao and situacao in situacoes_validas:
        qs = qs.filter(situacao=situacao)

    vinculos_validos = {choice.value for choice in FuncionarioRH.Vinculo}
    if vinculo and vinculo in vinculos_validos:
        qs = qs.filter(vinculo=vinculo)

    if setor:
        qs = qs.filter(setor_lotacao__icontains=setor)

    page_size_options = [10, 20, 30]
    try:
        page_size = int(request.GET.get('page_size', page_size_options[0]))
    except (TypeError, ValueError):
        page_size = page_size_options[0]
    if page_size not in page_size_options:
        page_size = page_size_options[0]

    paginator = Paginator(qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_range = list(page_obj.paginator.get_elided_page_range(number=page_obj.number))

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_string = query_params.urlencode()

    ctx = {
        'lista': page_obj.object_list,
        'page_obj': page_obj,
        'page_size': page_size,
        'page_size_options': page_size_options,
        'page_range': page_range,
        'query_string': query_string,
        'filter_nome': nome,
        'filter_cpf': cpf_raw,
        'filter_cargo': cargo,
        'filter_situacao': situacao,
        'filter_vinculo': vinculo,
        'filter_setor': setor,
        'situacao_choices': [(choice.value, choice.label) for choice in FuncionarioRH.Situacao],
        'vinculo_choices': [(choice.value, choice.label) for choice in FuncionarioRH.Vinculo],
    }
    return render(request, 'rh/funcionario_list.html', ctx)


@login_required
@require_access('rh')
def funcionario_create(request):
    if request.method == 'POST':
        form = FuncionarioRHForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário cadastrado com sucesso.')
            return redirect(reverse('rh-funcionario-list'))
        else:
            messages.error(request, 'Corrija os erros para salvar o funcionário.')
    else:
        form = FuncionarioRHForm()
    return render(request, 'rh/funcionario_form.html', {'form': form})


@login_required
@require_access('rh')
def funcionario_update(request, pk: int):
    obj = get_object_or_404(FuncionarioRH, pk=pk)
    if request.method == 'POST':
        form = FuncionarioRHForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados do funcionário atualizados.')
            return redirect(reverse('rh-funcionario-list'))
        else:
            messages.error(request, 'Corrija os erros antes de atualizar o funcionário.')
    else:
        form = FuncionarioRHForm(instance=obj)
    return render(request, 'rh/funcionario_form.html', {'form': form, 'obj': obj})


@login_required
@require_access('rh')
def funcionario_delete(request, pk: int):
    obj = get_object_or_404(FuncionarioRH, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Funcionário excluído com sucesso.')
        return redirect(reverse('rh-funcionario-list'))
    return render(request, 'rh/funcionario_confirm_delete.html', {'obj': obj})


@login_required
@require_access('rh')
def atestado_list(request):
    qs = AtestadoMedico.objects.select_related('funcionario', 'removido_por')
    if not request.user.is_superuser:
        qs = qs.filter(ativo=True)
    qs = qs.order_by('-ativo', '-data_inicio', '-criado_em')

    ctx = {
        'lista': qs,
        'exibe_acao_restaurar': request.user.is_superuser,
        'tem_removidos': request.user.is_superuser and AtestadoMedico.objects.filter(ativo=False).exists(),
    }
    return render(request, 'rh/atestado_list.html', ctx)


@login_required
@require_access('rh')
def atestado_create(request):
    funcionarios_info = {
        str(item['id']): {
            'nome': item['nome'],
            'cpf': item['cpf'],
            'cargo': item['cargo'],
            'setor_lotacao': item['setor_lotacao'] or ''
        }
        for item in FuncionarioRH.objects.values('id', 'nome', 'cpf', 'cargo', 'setor_lotacao')
    }

    if request.method == 'POST':
        form = AtestadoMedicoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atestado cadastrado com sucesso.')
            return redirect(reverse('rh-atestado-list'))
    else:
        form = AtestadoMedicoForm()
        # Pré-seleção de funcionário via querystring (?funcionario=<id>)
        try:
            fid = int(request.GET.get('funcionario') or 0)
        except (TypeError, ValueError):
            fid = 0
        if fid:
            form.initial['funcionario'] = fid
    return render(request, 'rh/atestado_form.html', {'form': form, 'funcionarios_info': funcionarios_info})


@login_required
@require_access('rh')
def atestado_update(request, pk: int):
    obj = get_object_or_404(AtestadoMedico, pk=pk)
    if not obj.ativo and not request.user.is_superuser:
        messages.error(request, 'Este atestado foi removido e só pode ser editado por administradores.')
        return redirect(reverse('rh-atestado-list'))

    if request.method == 'POST':
        form = AtestadoMedicoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atestado atualizado com sucesso.')
            return redirect(reverse('rh-atestado-list'))
        messages.error(request, 'Corrija os erros antes de salvar as alterações.')
    else:
        form = AtestadoMedicoForm(instance=obj)

    funcionarios_info = {
        str(item['id']): {
            'nome': item['nome'],
            'cpf': item['cpf'],
            'cargo': item['cargo'],
            'setor_lotacao': item['setor_lotacao'] or ''
        }
        for item in FuncionarioRH.objects.values('id', 'nome', 'cpf', 'cargo', 'setor_lotacao')
    }
    return render(request, 'rh/atestado_form.html', {'form': form, 'obj': obj, 'funcionarios_info': funcionarios_info})


@login_required
@require_access('rh')
@require_POST
def atestado_delete(request, pk: int):
    obj = get_object_or_404(AtestadoMedico, pk=pk)
    if not obj.ativo:
        messages.info(request, 'Este atestado já estava marcado como removido.')
        return redirect(reverse('rh-atestado-list'))

    obj.ativo = False
    obj.removido_em = timezone.now()
    obj.removido_por = request.user
    obj.save(update_fields=['ativo', 'removido_em', 'removido_por'])
    messages.success(request, 'Atestado removido. Apenas administradores podem visualizá-lo agora.')
    return redirect(reverse('rh-atestado-list'))


@login_required
@require_access('rh')
@require_POST
def atestado_restore(request, pk: int):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Apenas administradores podem restaurar atestados.')

    obj = get_object_or_404(AtestadoMedico, pk=pk)
    if obj.ativo:
        messages.info(request, 'Este atestado já está ativo.')
        return redirect(reverse('rh-atestado-list'))

    obj.ativo = True
    obj.removido_em = None
    obj.removido_por = None
    obj.save(update_fields=['ativo', 'removido_em', 'removido_por'])
    messages.success(request, 'Atestado restaurado com sucesso.')
    return redirect(reverse('rh-atestado-list'))


@login_required
@require_access('rh')
def atestado_print(request, pk: int):
    obj = get_object_or_404(AtestadoMedico.objects.select_related('funcionario'), pk=pk)
    if not obj.ativo and not request.user.is_superuser:
        messages.error(request, 'Este atestado está removido e só pode ser impresso por administradores.')
        return redirect(reverse('rh-atestado-list'))

    return render(request, 'rh/atestado_print.html', {'obj': obj})


@login_required
@require_access('rh')
def cid_lookup(request):
    code = (request.GET.get('code') or '').strip()
    normalized = code.upper().replace(' ', '')
    description = get_cid_description(normalized)
    return JsonResponse({
        'code': normalized,
        'description': description or '',
        'found': bool(description),
    })
