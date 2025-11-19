from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
	AbastecimentoForm,
	VeiculoForm,
	LocalManutencaoForm,
	ManutencaoVeiculoForm,
)
from .models import Abastecimento, Veiculo, LocalManutencao, ManutencaoVeiculo
from motorista.models import Motorista


@login_required
def abastecimento_list(request):
	qs = Abastecimento.objects.select_related("veiculo", "motorista").all().order_by('-data_hora')
	# Filtros: motorista, veiculo, período (início/fim)
	from django.utils.dateparse import parse_date
	motorista_id = (request.GET.get('motorista') or '').strip()
	veiculo_id = (request.GET.get('veiculo') or '').strip()
	inicio = (request.GET.get('inicio') or '').strip()
	fim = (request.GET.get('fim') or '').strip()
	start = parse_date(inicio) if inicio else None
	end = parse_date(fim) if fim else None
	if motorista_id:
		qs = qs.filter(motorista_id=motorista_id)
	if veiculo_id:
		qs = qs.filter(veiculo_id=veiculo_id)
	if start and end:
		qs = qs.filter(data_hora__date__gte=start, data_hora__date__lte=end)
	elif start:
		qs = qs.filter(data_hora__date=start)
	elif end:
		qs = qs.filter(data_hora__date=end)
	show_deleted = request.user.is_superuser
	if not show_deleted:
		qs = qs.filter(excluido_em__isnull=True)

	motoristas = Motorista.objects.all().order_by('nome_completo')
	veiculos = Veiculo.objects.all().order_by('modelo')

	paginator = Paginator(qs, 10)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	page_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)

	query_params = request.GET.copy()
	query_params.pop('page', None)
	base_query = query_params.urlencode()
	if base_query:
		base_query += '&'

	ctx = {
		"lista": page_obj,
		"page_obj": page_obj,
		"paginator": paginator,
		"page_range": page_range,
		"is_paginated": page_obj.has_other_pages(),
		"pagination_query": base_query,
		"show_deleted": show_deleted,
		"motoristas": motoristas,
		"veiculos": veiculos,
		"filtros": {"motorista": motorista_id, "veiculo": veiculo_id, "inicio": inicio, "fim": fim},
	}
	return render(request, "veiculos/abastecimento_list.html", ctx)


@login_required
def abastecimento_create(request):
	if request.method == "POST":
		form = AbastecimentoForm(request.POST)
		if form.is_valid():
			abastecimento = form.save(commit=False)
			abastecimento.registrado_por = request.user
			abastecimento.save()
			messages.success(request, "Abastecimento registrado com sucesso.")
			return redirect(reverse("abastecimento-list"))
		else:
			messages.error(request, "Corrija os erros para salvar o abastecimento.")
	else:
		form = AbastecimentoForm()
	return render(request, "veiculos/abastecimento_form.html", {"form": form})


@login_required
def abastecimento_print(request, pk: int):
	registro = get_object_or_404(
		Abastecimento.objects.select_related("veiculo", "motorista", "registrado_por"),
		pk=pk,
	)
	if registro.excluido_em and not request.user.is_superuser:
		messages.error(request, "Este abastecimento foi excluído e não pode ser impresso.")
		return redirect(reverse("abastecimento-list"))
	return render(request, "veiculos/abastecimento_print.html", {"a": registro})


@login_required
def abastecimento_update(request, pk: int):
	obj = get_object_or_404(Abastecimento, pk=pk)
	if obj.excluido_em and not request.user.is_superuser:
		messages.error(request, "Este abastecimento foi excluído e não pode ser editado.")
		return redirect(reverse("abastecimento-list"))
	if request.method == "POST":
		form = AbastecimentoForm(request.POST, instance=obj)
		if form.is_valid():
			form.save()
			messages.success(request, "Abastecimento atualizado com sucesso.")
			return redirect(reverse("abastecimento-list"))
		else:
			messages.error(request, "Corrija os erros para atualizar o abastecimento.")
	else:
		form = AbastecimentoForm(instance=obj)
	return render(request, "veiculos/abastecimento_form.html", {"form": form, "obj": obj})


@login_required
def abastecimento_delete(request, pk: int):
	obj = get_object_or_404(Abastecimento, pk=pk)
	if request.method == "POST":
		if request.user.is_superuser and request.POST.get("permanent") == "1":
			obj.delete()
			messages.success(request, "Abastecimento excluído permanentemente.")
			return redirect(reverse("abastecimento-list"))

		if obj.excluido_em is None:
			obj.excluido_em = timezone.now()
			obj.excluido_por = request.user
			obj.save(update_fields=["excluido_em", "excluido_por"])
			messages.success(request, "Abastecimento marcado como excluído. Somente administradores podem vê-lo.")
		else:
			messages.info(request, "Este abastecimento já estava marcado como excluído.")
		return redirect(reverse("abastecimento-list"))

	contexto = {
		"obj": obj,
		"pode_excluir_definitivo": request.user.is_superuser,
		"ja_excluido": obj.excluido_em is not None,
	}
	return render(request, "veiculos/abastecimento_confirm_delete.html", contexto)

@login_required
def abastecimento_restore(request, pk: int):
	obj = get_object_or_404(Abastecimento, pk=pk)
	if not request.user.is_superuser:
		messages.error(request, "Apenas administradores podem restaurar abastecimentos excluídos.")
		return redirect(reverse("abastecimento-list"))
	if obj.excluido_em is None:
		messages.info(request, "Este abastecimento já está ativo.")
		return redirect(reverse("abastecimento-list"))
	if request.method == "POST":
		obj.excluido_em = None
		obj.excluido_por = None
		obj.save(update_fields=["excluido_em", "excluido_por"])
		messages.success(request, "Abastecimento restaurado com sucesso.")
	return redirect(reverse("abastecimento-list"))


# --- Manutenções ---


@login_required
def manutencao_list(request):
	qs = (
		ManutencaoVeiculo.objects.select_related("veiculo", "local")
		.order_by("-data_envio", "-id")
	)
	veiculo_id = (request.GET.get("veiculo") or "").strip()
	status = (request.GET.get("status") or "").strip()
	if veiculo_id:
		qs = qs.filter(veiculo_id=veiculo_id)
	if status:
		qs = qs.filter(status=status)

	veiculos = Veiculo.objects.order_by("modelo")
	contexto = {
		"manutencoes": qs,
		"veiculos": veiculos,
		"filtros": {"veiculo": veiculo_id, "status": status},
		"status_choices": ManutencaoVeiculo.STATUS_CHOICES,
	}
	return render(request, "veiculos/manutencao_list.html", contexto)


@login_required
def manutencao_create(request):
	if request.method == "POST":
		form = ManutencaoVeiculoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "Manutenção registrada com sucesso.")
			return redirect(reverse("manutencao-list"))
	else:
		form = ManutencaoVeiculoForm()
	return render(request, "veiculos/manutencao_form.html", {"form": form})


@login_required
def manutencao_update(request, pk: int):
	manutencao = get_object_or_404(ManutencaoVeiculo, pk=pk)
	if request.method == "POST":
		form = ManutencaoVeiculoForm(request.POST, instance=manutencao)
		if form.is_valid():
			manutencao_atualizado = form.save(commit=False)
			manutencao_atualizado.data_envio = manutencao.data_envio
			manutencao_atualizado.save()
			messages.success(request, "Manutenção atualizada com sucesso.")
			return redirect(reverse("manutencao-list"))
	else:
		form = ManutencaoVeiculoForm(instance=manutencao)
	return render(
		request,
		"veiculos/manutencao_form.html",
		{"form": form, "obj": manutencao},
	)


@login_required
def manutencao_detail(request, pk: int):
	manutencao = get_object_or_404(
		ManutencaoVeiculo.objects.select_related("veiculo", "local"), pk=pk
	)
	veiculo = manutencao.veiculo
	try:
		from viagens.models import Viagem
	except ImportError:
		Viagem = None

	if Viagem is not None:
		viagens = (
			Viagem.objects.select_related("paciente")
			.filter(veiculo=veiculo)
			.order_by("-data_viagem")[:10]
		)
	else:
		viagens = []
	abastecimentos = veiculo.abastecimentos.select_related("motorista").order_by("-data_hora")[:10]
	contexto = {
		"obj": manutencao,
		"veiculo": veiculo,
		"viagens": viagens,
		"abastecimentos": abastecimentos,
	}
	return render(request, "veiculos/manutencao_detail.html", contexto)


@login_required
def manutencao_finalize(request, pk: int):
	manutencao = get_object_or_404(ManutencaoVeiculo, pk=pk)
	if request.method == "POST":
		data_retorno = request.POST.get("data_retorno")
		servicos = request.POST.get("servicos_realizados")
		if data_retorno:
			try:
				data_retorno = datetime.strptime(data_retorno, "%Y-%m-%d").date()
			except ValueError:
				messages.error(request, "Data de devolução inválida.")
				return redirect(reverse("manutencao-list"))
			if data_retorno < manutencao.data_envio:
				messages.error(request, "A data de devolução não pode ser anterior à data de envio.")
				return redirect(reverse("manutencao-list"))
			manutencao.data_retorno = data_retorno
		if servicos:
			manutencao.servicos_realizados = servicos
		manutencao.status = "concluida"
		manutencao.save(update_fields=["data_retorno", "servicos_realizados", "status", "atualizado_em"])
		messages.success(request, "Manutenção marcada como concluída.")
	else:
		messages.info(request, "Utilize o formulário para concluir a manutenção.")
	return redirect(reverse("manutencao-list"))


@login_required
def manutencao_print(request, pk: int):
	manutencao = get_object_or_404(
		ManutencaoVeiculo.objects.select_related("veiculo", "local"), pk=pk
	)
	return render(request, "veiculos/manutencao_print.html", {"obj": manutencao})


# --- Locais de manutenção ---


@login_required
def local_manutencao_list(request):
	qs = LocalManutencao.objects.all()
	return render(request, "veiculos/localmanutencao_list.html", {"locais": qs})


@login_required
def local_manutencao_create(request):
	if request.method == "POST":
		form = LocalManutencaoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "Local de manutenção cadastrado.")
			return redirect(reverse("local-manutencao-list"))
	else:
		form = LocalManutencaoForm()
	return render(request, "veiculos/localmanutencao_form.html", {"form": form})


@login_required
def local_manutencao_update(request, pk: int):
	obj = get_object_or_404(LocalManutencao, pk=pk)
	if request.method == "POST":
		form = LocalManutencaoForm(request.POST, instance=obj)
		if form.is_valid():
			form.save()
			messages.success(request, "Local de manutenção atualizado.")
			return redirect(reverse("local-manutencao-list"))
	else:
		form = LocalManutencaoForm(instance=obj)
	return render(request, "veiculos/localmanutencao_form.html", {"form": form, "obj": obj})


@login_required
def local_manutencao_delete(request, pk: int):
	obj = get_object_or_404(LocalManutencao, pk=pk)
	if request.method == "POST":
		if obj.manutencoes.exists():
			messages.error(request, "Não é possível excluir: existem manutenções vinculadas a este local.")
			return redirect(reverse("local-manutencao-list"))
		obj.delete()
		messages.success(request, "Local de manutenção removido.")
		return redirect(reverse("local-manutencao-list"))
	return render(
		request,
		"veiculos/localmanutencao_confirm_delete.html",
		{"obj": obj},
	)

# --- Veículo (lista e cadastro rápido) ---
@login_required
def veiculo_list(request):
	qs = Veiculo.objects.select_related('motorista').all().order_by('modelo')
	return render(request, 'veiculos/veiculo_list.html', {'veiculos': qs})


@login_required
def veiculo_create(request):
	if request.method == 'POST':
		form = VeiculoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Veículo cadastrado com sucesso.')
			return redirect('veiculo-list')
	else:
		form = VeiculoForm()
	return render(request, 'veiculos/veiculo_form.html', {'form': form})


@login_required
def veiculo_update(request, pk: int):
	obj = get_object_or_404(Veiculo, pk=pk)
	if request.method == 'POST':
		form = VeiculoForm(request.POST, instance=obj)
		if form.is_valid():
			form.save()
			messages.success(request, 'Veículo atualizado com sucesso.')
			return redirect('veiculo-list')
	else:
		form = VeiculoForm(instance=obj)
	return render(request, 'veiculos/veiculo_form.html', {'form': form, 'obj': obj})


@login_required
def veiculo_delete(request, pk: int):
	obj = get_object_or_404(Veiculo, pk=pk)
	has_abastecimentos = obj.abastecimentos.exists()
	if request.method == 'POST':
		if has_abastecimentos:
			messages.error(request, 'Este veículo possui abastecimentos vinculados e não pode ser excluído.')
			return redirect('veiculo-delete', pk=obj.pk)
		try:
			obj.delete()
			messages.success(request, 'Veículo excluído com sucesso.')
		except ProtectedError:
			messages.error(request, 'Não foi possível excluir: existem registros vinculados (abastecimentos).')
		return redirect('veiculo-list')
	return render(
		request,
		'veiculos/veiculo_confirm_delete.html',
		{
			'obj': obj,
			'can_delete': not has_abastecimentos,
			'related_count': obj.abastecimentos.count(),
		},
	)
