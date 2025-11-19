from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from secretaria_it.access import require_access

from .models import Motorista, ViagemMotorista
from .forms import MotoristaForm, ViagemMotoristaForm
from rh.models import FuncionarioRH


def _get_rh_motoristas_queryset():
    return FuncionarioRH.objects.filter(cargo__icontains='motorista').order_by('nome')


def _build_rh_motoristas_context(request):
    qs = _get_rh_motoristas_queryset()
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('rh_page') or request.POST.get('rh_page') or 1
    page_obj = paginator.get_page(page_number)
    return {
        'rh_motoristas_page': page_obj,
        'rh_motoristas_total': paginator.count,
    }


@login_required
@require_access('motorista')
def motorista_home(request):
    from django.utils import timezone
    from veiculos.models import ManutencaoVeiculo

    today = timezone.localdate()
    month_start = today.replace(day=1)
    total_motoristas = Motorista.objects.count()
    total_viagens_mes = ViagemMotorista.objects.filter(
        data_inicio__gte=month_start,
        data_inicio__lte=today,
    ).count()
    manutencoes_abertas = ManutencaoVeiculo.objects.filter(
        status__in=("pendente", "em_andamento"),
    ).count()
    ctx = {
        'total_motoristas': total_motoristas,
        'total_viagens_mes': total_viagens_mes,
        'manutencoes_abertas': manutencoes_abertas,
    }
    return render(request, 'motorista/home.html', ctx)


@login_required
@require_access('motorista')
def motorista_list(request):
    qs = Motorista.objects.all().order_by('nome_completo')
    return render(request, 'motorista/motorista_list.html', {'motoristas': qs})


@login_required
@require_access('motorista')
def motorista_create(request):
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista cadastrado com sucesso.')
            # Após salvar, ir para a lista de motoristas conforme solicitado
            return redirect('motorista-list')
        else:
            messages.error(request, 'Corrija os erros para salvar o motorista.')
    else:
        form = MotoristaForm()
    ctx = {
        'form': form,
    }
    ctx.update(_build_rh_motoristas_context(request))
    return render(request, 'motorista/motorista_form.html', ctx)


@login_required
@require_access('motorista')
def motorista_update(request, pk):
    obj = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso.')
            return redirect('motorista-list')
        else:
            messages.error(request, 'Corrija os erros para atualizar o motorista.')
    else:
        form = MotoristaForm(instance=obj)
    ctx = {
        'form': form,
        'obj': obj,
    }
    ctx.update(_build_rh_motoristas_context(request))
    return render(request, 'motorista/motorista_form.html', ctx)


@login_required
@require_access('motorista')
def motorista_delete(request, pk):
    obj = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Motorista excluído com sucesso.')
    return redirect('motorista-list')


@login_required
@require_access('motorista')
def viagem_list(request):
    from django.utils.dateparse import parse_date
    qs = ViagemMotorista.objects.select_related('motorista', 'veiculo').all()
    motorista_id = (request.GET.get('motorista') or '').strip()
    veiculo_id = (request.GET.get('veiculo') or '').strip()
    destino = (request.GET.get('destino') or '').strip()
    inicio = (request.GET.get('inicio') or '').strip()
    fim = (request.GET.get('fim') or '').strip()
    start = parse_date(inicio) if inicio else None
    end = parse_date(fim) if fim else None
    if motorista_id:
        qs = qs.filter(motorista_id=motorista_id)
    if veiculo_id:
        qs = qs.filter(veiculo_id=veiculo_id)
    if destino:
        qs = qs.filter(destino__icontains=destino)
    if start and end:
        qs = qs.filter(data_inicio__gte=start, data_fim__lte=end)
    elif start:
        qs = qs.filter(data_inicio__gte=start)
    elif end:
        qs = qs.filter(data_fim__lte=end)
    qs = qs.order_by('-data_inicio', '-id')

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    query_dict = request.GET.copy()
    query_dict.pop('page', None)
    query_string = query_dict.urlencode()

    motoristas = Motorista.objects.all().order_by('nome_completo')
    from veiculos.models import Veiculo as VeiculoModel
    veiculos = VeiculoModel.objects.all().order_by('modelo')
    ctx = {
        'viagens': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'query_string': query_string,
        'motoristas': motoristas,
        'veiculos': veiculos,
        'filtros': {
            'motorista': motorista_id,
            'veiculo': veiculo_id,
            'destino': destino,
            'inicio': inicio,
            'fim': fim,
        }
    }
    return render(request, 'motorista/viagem_list.html', ctx)


@login_required
@require_access('motorista')
def viagem_print(request):
    """Página de impressão com colunas solicitadas."""
    destinos_disponiveis = [
        destino for destino in (
            ViagemMotorista.objects
            .order_by('destino')
            .values_list('destino', flat=True)
            .distinct()
        ) if destino
    ]
    destinos_selecionados = [d for d in request.GET.getlist('destinos') if d]

    qs = ViagemMotorista.objects.select_related('motorista', 'veiculo')
    if destinos_selecionados:
        qs = qs.filter(destino__in=destinos_selecionados)

    qs = qs.order_by('destino', 'data_inicio', 'id')
    contexto = {
        'viagens': qs,
        'destinos_disponiveis': destinos_disponiveis,
        'destinos_selecionados': destinos_selecionados,
    }
    return render(request, 'motorista/viagem_print.html', contexto)


@login_required
@require_access('motorista')
def viagem_print_single(request, pk):
    """Impressão individual de uma viagem."""
    v = get_object_or_404(ViagemMotorista.objects.select_related('motorista', 'veiculo'), pk=pk)
    return render(request, 'motorista/viagem_print_single.html', {'v': v})


@login_required
@require_access('motorista')
def viagem_create(request):
    if request.method == 'POST':
        form = ViagemMotoristaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Viagem registrada com sucesso.')
            return redirect('motorista-viagem-list')
        else:
            messages.error(request, 'Corrija os erros para salvar a viagem.')
    else:
        form = ViagemMotoristaForm()
    return render(request, 'motorista/viagem_form.html', {'form': form})


@login_required
@require_access('motorista')
def viagem_update(request, pk):
    obj = get_object_or_404(ViagemMotorista, pk=pk)
    if request.method == 'POST':
        form = ViagemMotoristaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Viagem atualizada com sucesso.')
            return redirect('motorista-viagem-list')
        else:
            messages.error(request, 'Corrija os erros para atualizar a viagem.')
    else:
        form = ViagemMotoristaForm(instance=obj)
    return render(request, 'motorista/viagem_form.html', {'form': form, 'obj': obj})


@login_required
@require_access('motorista')
def viagem_delete(request, pk):
    obj = get_object_or_404(ViagemMotorista, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Viagem excluída com sucesso.')
        return redirect('motorista-viagem-list')
    return render(request, 'motorista/viagem_confirm_delete.html', {'obj': obj})


@login_required
@require_access('motorista')
def relatorios_view(request):
    # Filtros simples por período
    from django.db.models import Sum, Count
    from django.utils.dateparse import parse_date

    inicio = (request.GET.get('inicio') or '').strip()
    fim = (request.GET.get('fim') or '').strip()
    start = parse_date(inicio) if inicio else None
    end = parse_date(fim) if fim else None

    qs = ViagemMotorista.objects.all()
    if start:
        qs = qs.filter(data_inicio__gte=start)
    if end:
        qs = qs.filter(data_fim__lte=end)

    # Relatórios
    total_por_motorista = (
        qs.values('motorista__nome_completo')
          .annotate(total=Count('id'))
          .order_by('-total')
    )
    gastos_diarias = qs.aggregate(
        total_diarias=Sum('valor_total_diarias')
    )
    gastos_horas_extras = qs.aggregate(
        total_horas_extras=Sum('valor_total_horas_extras')
    )
    quantidades = qs.aggregate(
        qtd_diarias=Sum('quantidade_diarias'),
        qtd_horas_extras=Sum('quantidade_horas_extras')
    )
    ranking_motoristas = total_por_motorista[:10]

    justificativas_recorrentes = (
        qs.values('justificativa_horas_extras')
          .exclude(justificativa_horas_extras='')
          .annotate(total=Count('id'))
          .order_by('-total')[:10]
    )

    context = {
        'total_por_motorista': total_por_motorista,
    'gastos_diarias': gastos_diarias.get('total_diarias') or 0,
    'gastos_horas_extras': gastos_horas_extras.get('total_horas_extras') or 0,
    'total_qtd_diarias': quantidades.get('qtd_diarias') or 0,
    'total_qtd_horas_extras': quantidades.get('qtd_horas_extras') or 0,
        'ranking_motoristas': ranking_motoristas,
        'justificativas_recorrentes': justificativas_recorrentes,
        'inicio': inicio,
        'fim': fim,
    }
    return render(request, 'motorista/relatorios.html', context)
