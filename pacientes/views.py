from django.contrib.auth.mixins import LoginRequiredMixin
from secretaria_it.access import AccessRequiredMixin, user_has_access, is_ubs_user
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente
from regulacao.models import RegulacaoExame, RegulacaoConsulta
from regulacao.models import UBS, TipoExame, Especialidade
from viagens.models import Viagem
from tfd.models import TFD
from django.utils.dateparse import parse_date
from django.utils.http import urlencode
from .forms import PacienteForm
from .services import buscar_paciente_esus
from collections import defaultdict

class PacienteListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    # Ampliar permissão: permitir lista para 'pacientes' OU 'regulacao' OU usuário UBS
    model = Paciente
    template_name = "pacientes/paciente_list.html"
    context_object_name = "pacientes"
    ordering = ["nome"]
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (
            user_has_access(request.user, 'pacientes') or
            user_has_access(request.user, 'regulacao') or
            is_ubs_user(request.user)
        ):
            return HttpResponseForbidden('Acesso negado para visualizar pacientes.')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q)
                | Q(cpf__icontains=q)
                | Q(cns__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        return ctx


@login_required
def paciente_autocomplete(request):
    # Permitir autocomplete se usuário tiver acesso a Pacientes OU a Regulação
    if not (user_has_access(request.user, 'pacientes') or user_has_access(request.user, 'regulacao')):
        return JsonResponse({"results": []})
    q = (request.GET.get("q") or "").strip()
    limit = int(request.GET.get("limit") or 20)
    limit = max(1, min(limit, 50))
    qs = Paciente.objects.all()
    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cpf__icontains=q)
            | Q(cns__icontains=q)
        )
    qs = qs.order_by("nome").values(
        "id",
        "nome",
        "cpf",
        "cns",
        "telefone",
        "logradouro",
        "numero",
        "bairro",
        "cep",
    )[:limit]
    results = []
    for r in qs:
        label_parts = [r.get("nome") or ""]
        if r.get("cpf"):
            label_parts.append(f"CPF: {r['cpf']}")
        if r.get("cns"):
            label_parts.append(f"CNS: {r['cns']}")
        endereco_parts = []
        if r.get("logradouro"):
            endereco_parts.append(r["logradouro"])
        if r.get("numero"):
            endereco_parts.append(f"nº {r['numero']}")
        if r.get("bairro"):
            endereco_parts.append(r["bairro"])
        if r.get("cep"):
            endereco_parts.append(f"CEP: {r['cep']}")
        endereco_text = ", ".join(part for part in endereco_parts if part)
        results.append({
            "id": r["id"],
            "nome": r["nome"],
            "cpf": r.get("cpf"),
            "cns": r.get("cns"),
            "telefone": r.get("telefone") or "",
            "logradouro": r.get("logradouro") or "",
            "numero": r.get("numero") or "",
            "bairro": r.get("bairro") or "",
            "cep": r.get("cep") or "",
            "endereco": endereco_text,
            "label": " | ".join(p for p in label_parts if p),
        })
    return JsonResponse({"results": results})

class PacienteCreateView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    # Permitir criar paciente para quem tem acesso a 'pacientes' OU 'regulacao' OU for usuário UBS
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        # LoginRequiredMixin já garante autenticação; aqui garantimos permissão ampliada
        if not (
            user_has_access(request.user, 'pacientes') or
            user_has_access(request.user, 'regulacao') or
            is_ubs_user(request.user)
        ):
            return HttpResponseForbidden('Acesso negado para criar paciente.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Paciente criado com sucesso.")
        return response

    def get_initial(self):
        """Se vier cpf/cns via GET, tenta buscar no e-SUS e preencher o formulário.

        Não salva nada automaticamente, apenas pré-preenche os campos.
        """
        initial = super().get_initial()
        cpf = (self.request.GET.get('cpf') or '').strip()
        cns = (self.request.GET.get('cns') or '').strip()
        try:
            dados = buscar_paciente_esus(cpf=cpf or None, cns=cns or None)
            if dados:
                initial.update({
                    'nome': dados.get('nome') or '',
                    'cpf': dados.get('cpf') or '',
                    'cns': dados.get('cns') or '',
                    'data_nascimento': dados.get('data_nascimento'),
                    'nome_mae': dados.get('nome_mae') or '',
                    'nome_pai': dados.get('nome_pai') or '',
                    'telefone': dados.get('telefone') or '',
                    'logradouro': dados.get('logradouro') or '',
                    'numero': dados.get('numero') or '',
                    'bairro': dados.get('bairro') or '',
                    'cep': dados.get('cep') or '',
                })
        except Exception:
            pass
        return initial

class PacienteUpdateView(AccessRequiredMixin, LoginRequiredMixin, UpdateView):
    login_url = '/accounts/login/'
    access_key = 'pacientes'
    model = Paciente
    form_class = PacienteForm
    template_name = "pacientes/paciente_form.html"
    success_url = reverse_lazy("paciente_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Paciente atualizado com sucesso!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar paciente. Verifique os dados.')
        return super().form_invalid(form)

    def get_initial(self):
        """Opcionalmente pré-preenche campos vazios com dados do e-SUS quando ?esus=1.

        Útil para complementar cadastro existente sem sobrescrever manualmente.
        """
        initial = super().get_initial()
        try:
            if self.request.GET.get('esus') == '1':
                cpf = (self.object.cpf or '').strip()
                cns = (self.object.cns or '').strip()
                dados = buscar_paciente_esus(cpf=cpf or None, cns=cns or None)
                if dados:
                    # Só aplica initial para campos que estejam vazios no instance
                    for f in ['nome','cpf','cns','data_nascimento','nome_mae','nome_pai','telefone','logradouro','numero','bairro','cep']:
                        if not getattr(self.object, f, None):
                            initial[f] = dados.get(f)
                    # Adiciona mensagem de sucesso se dados foram encontrados
                    messages.success(self.request, 'Dados do e-SUS carregados com sucesso para campos vazios!')
                else:
                    # Mensagem se não encontrou dados
                    messages.warning(self.request, 'Nenhum dado encontrado no e-SUS para este CPF/CNS.')
        except Exception as e:
            messages.error(self.request, f'Erro ao buscar dados no e-SUS: {str(e)}')
        return initial

class PacienteDeleteView(AccessRequiredMixin, LoginRequiredMixin, DeleteView):
    login_url = '/accounts/login/'
    access_key = 'pacientes'
    model = Paciente
    template_name = "pacientes/paciente_confirm_delete.html"
    success_url = reverse_lazy("paciente_list")

    def post(self, request, *args, **kwargs):
        # Override POST to add success message after deletion
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Paciente excluído com sucesso.")
        return response


class PacienteHistoricoView(AccessRequiredMixin, LoginRequiredMixin, DetailView):
    login_url = '/accounts/login/'
    access_key = 'pacientes'
    model = Paciente
    template_name = 'pacientes/paciente_historico.html'
    context_object_name = 'paciente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paciente = self.object
        from django.utils import timezone
        ctx['hoje'] = timezone.localdate()

        # Filtros: período e texto livre (destino/hospital/observações, etc.)
        start = self.request.GET.get('inicio')
        end = self.request.GET.get('fim')
        q = (self.request.GET.get('q') or '').strip()
        # Filtros por seção
        status_ex = (self.request.GET.get('status_ex') or '').strip()
        ubs_ex = (self.request.GET.get('ubs_ex') or '').strip()
        tipo_exame_ex = (self.request.GET.get('tipo_exame_ex') or '').strip()
        status_co = (self.request.GET.get('status_co') or '').strip()
        ubs_co = (self.request.GET.get('ubs_co') or '').strip()
        especialidade_co = (self.request.GET.get('especialidade_co') or '').strip()

        s = parse_date(start) if start else None
        e = parse_date(end) if end else None

    # Exames
        exames = RegulacaoExame.objects.select_related('tipo_exame', 'ubs_solicitante').filter(paciente=paciente)
        if s:
            exames = exames.filter(data_solicitacao__date__gte=s)
        if e:
            exames = exames.filter(data_solicitacao__date__lte=e)
        if q:
            exames = exames.filter(
                Q(tipo_exame__nome__icontains=q)
                | Q(ubs_solicitante__nome__icontains=q)
                | Q(observacoes_solicitacao__icontains=q)
                | Q(observacoes_regulacao__icontains=q)
                | Q(motivo_decisao__icontains=q)
            )
        if status_ex:
            if status_ex == 'agendados':
                exames = exames.filter(status='autorizado', data_agendada__isnull=False)
            else:
                exames = exames.filter(status=status_ex)
        if ubs_ex:
            try:
                exames = exames.filter(ubs_solicitante_id=int(ubs_ex))
            except (TypeError, ValueError):
                pass
        if tipo_exame_ex:
            try:
                exames = exames.filter(tipo_exame_id=int(tipo_exame_ex))
            except (TypeError, ValueError):
                pass
        exames = exames.order_by('-data_solicitacao')

        # Grupos de impressão (exames autorizados por data agendada)
        ex_groups_map = defaultdict(list)
        for rid, d in (
            RegulacaoExame.objects
            .filter(paciente=paciente, status='autorizado', data_agendada__isnull=False)
            .values_list('id', 'data_agendada')
        ):
            ex_groups_map[d].append(rid)
        ex_print_groups = [
            {
                'date': d,
                'ids_csv': ",".join(str(i) for i in ids),
                'count': len(ids),
            }
            for d, ids in sorted(ex_groups_map.items(), key=lambda x: x[0], reverse=True)
        ]

        # IDs CSV para imprimir todos os exames autorizados visíveis no histórico
        ex_aut_ids_csv = ",".join(str(i) for i in exames.filter(status='autorizado').values_list('id', flat=True))

        # Consultas
        consultas = RegulacaoConsulta.objects.select_related('especialidade', 'ubs_solicitante').filter(paciente=paciente)
        if s:
            consultas = consultas.filter(data_solicitacao__date__gte=s)
        if e:
            consultas = consultas.filter(data_solicitacao__date__lte=e)
        if q:
            consultas = consultas.filter(
                Q(especialidade__nome__icontains=q)
                | Q(ubs_solicitante__nome__icontains=q)
                | Q(observacoes_solicitacao__icontains=q)
                | Q(observacoes_regulacao__icontains=q)
                | Q(motivo_decisao__icontains=q)
            )
        if status_co:
            if status_co == 'agendados':
                consultas = consultas.filter(status='autorizado', data_agendada__isnull=False)
            else:
                consultas = consultas.filter(status=status_co)
        if ubs_co:
            try:
                consultas = consultas.filter(ubs_solicitante_id=int(ubs_co))
            except (TypeError, ValueError):
                pass
        if especialidade_co:
            try:
                consultas = consultas.filter(especialidade_id=int(especialidade_co))
            except (TypeError, ValueError):
                pass
        consultas = consultas.order_by('-data_solicitacao')

        # Grupos de impressão (consultas autorizadas por data agendada)
        co_groups_map = defaultdict(list)
        for cid, d in (
            RegulacaoConsulta.objects
            .filter(paciente=paciente, status='autorizado', data_agendada__isnull=False)
            .values_list('id', 'data_agendada')
        ):
            co_groups_map[d].append(cid)
        co_print_groups = [
            {
                'date': d,
                'ids_csv': ",".join(str(i) for i in ids),
                'count': len(ids),
            }
            for d, ids in sorted(co_groups_map.items(), key=lambda x: x[0], reverse=True)
        ]

        # Viagens
        viagens = Viagem.objects.select_related('paciente','veiculo').filter(paciente=paciente)
        if s:
            viagens = viagens.filter(data_viagem__gte=s)
        if e:
            viagens = viagens.filter(data_viagem__lte=e)
        if q:
            viagens = viagens.filter(
                Q(destino__icontains=q) |
                Q(hospital__icontains=q) |
                Q(tipo_atendimento__icontains=q) |
                Q(observacoes__icontains=q)
            )
        viagens = viagens.order_by('-data_viagem')

        # TFD (considera tanto vinculado quanto snapshot por cpf/nome)
        tfds = TFD.objects.all()
        # Prioriza FK
        tfds = tfds.filter(Q(paciente=paciente) | Q(paciente__isnull=True))
        # ampliar por snapshot quando existir correspondência
        if paciente.cpf:
            tfds = tfds | TFD.objects.filter(paciente_cpf=paciente.cpf)
        tfds = tfds.distinct()
        if s:
            tfds = tfds.filter(data_inicio__gte=s)
        if e:
            tfds = tfds.filter(data_fim__lte=e) | tfds.filter(data_fim__isnull=True, data_inicio__lte=e)
        if q:
            tfds = tfds.filter(
                Q(paciente_nome__icontains=q) |
                Q(cidade_destino__icontains=q) |
                Q(observacoes__icontains=q)
            )
        tfds = tfds.order_by('-data_inicio','-criado_em')

        # Paginação independente por seção
        from django.core.paginator import Paginator
        page_ex = self.request.GET.get('page_ex') or 1
        page_co = self.request.GET.get('page_co') or 1
        page_vi = self.request.GET.get('page_vi') or 1
        page_tfd = self.request.GET.get('page_tfd') or 1
        ex_page = Paginator(exames, 10).get_page(page_ex)
        co_page = Paginator(consultas, 10).get_page(page_co)
        vi_page = Paginator(viagens, 10).get_page(page_vi)
        tfd_page = Paginator(tfds, 10).get_page(page_tfd)

        # Querystrings sem os parâmetros de paginação de cada seção
        def build_qs(exclude_keys):
            params = []
            for k in self.request.GET.keys():
                if k in exclude_keys:
                    continue
                for v in self.request.GET.getlist(k):
                    params.append((k, v))
            return urlencode(params)

        ctx.update({
            'ex_page': ex_page,
            'co_page': co_page,
            'vi_page': vi_page,
            'tfd_page': tfd_page,
            'ex_print_groups': ex_print_groups,
            'co_print_groups': co_print_groups,
            'ex_aut_ids_csv': ex_aut_ids_csv,
            'inicio': start or '',
            'fim': end or '',
            'q': q,
            'status_ex': status_ex,
            'ubs_ex': ubs_ex,
            'tipo_exame_ex': tipo_exame_ex,
            'status_co': status_co,
            'ubs_co': ubs_co,
            'especialidade_co': especialidade_co,
            'ubs_list': UBS.objects.filter(ativa=True).order_by('nome'),
            'tipoexame_list': TipoExame.objects.filter(ativo=True).order_by('nome'),
            'especialidades': Especialidade.objects.filter(ativa=True).order_by('nome'),
            'qs_ex': build_qs({'page_ex'}),
            'qs_co': build_qs({'page_co'}),
            'qs_vi': build_qs({'page_vi'}),
            'qs_tfd': build_qs({'page_tfd'}),
        })
        return ctx
