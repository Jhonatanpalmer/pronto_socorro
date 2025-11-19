from django.contrib.auth.mixins import LoginRequiredMixin
from secretaria_it.access import AccessRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.db.models import Q, Sum, Value, F
from django.db.models.functions import Coalesce, Replace
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import TFD
from pacientes.models import Paciente
from pacientes.services import buscar_paciente_esus, atualizar_paciente_com_esus
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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limitar a escolha do paciente a apenas um (via ?paciente=ID)
        try:
            pid = int(self.request.GET.get('paciente') or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid:
            form.fields['paciente'].queryset = Paciente.objects.filter(pk=pid)
            form.fields['paciente'].empty_label = None
            if not form.initial.get('paciente'):
                form.initial['paciente'] = pid
        # Removido o else que limitava o queryset - deixar o formulário gerenciar isso
        return form

    def get_initial(self):
        initial = super().get_initial()
        # Pré-preencher snapshot a partir do paciente informado
        try:
            pid = int(self.request.GET.get('paciente') or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid:
            try:
                p = Paciente.objects.filter(pk=pid).first()
                if p:
                    if p.cpf:
                        initial.setdefault('paciente_cpf', p.cpf)
                    if p.cns:
                        initial.setdefault('paciente_cns', p.cns)
                    # Montar endereço completo a partir dos campos estruturados
                    endereco_parts = []
                    if getattr(p, 'logradouro', None):
                        endereco_parts.append(p.logradouro)
                    if getattr(p, 'numero', None):
                        endereco_parts.append(f"nº {p.numero}")
                    if getattr(p, 'bairro', None):
                        endereco_parts.append(p.bairro)
                    if getattr(p, 'cep', None):
                        endereco_parts.append(f"CEP: {p.cep}")
                    
                    if endereco_parts:
                        endereco_completo = ", ".join(endereco_parts)
                        initial.setdefault('paciente_endereco', endereco_completo)
                    if p.telefone:
                        initial.setdefault('paciente_telefone', p.telefone)
            except Exception:
                pass
        return initial

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

def _cpf_digits_expression(field_name='cpf'):
    expr = F(field_name)
    for ch in ['.', '-', ' ', '/', '\\']:
        expr = Replace(expr, Value(ch), Value(''))
    return expr


@login_required
@require_http_methods(["GET"])
def buscar_paciente_por_cpf(request):
    """
    AJAX endpoint para buscar paciente por CPF e carregar dados do e-SUS se necessário
    """
    cpf = request.GET.get('cpf', '').strip()
    
    if not cpf:
        return JsonResponse({'error': 'CPF é obrigatório'}, status=400)
    
    # Remover formatação do CPF
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) != 11:
        return JsonResponse({'error': 'CPF deve ter 11 dígitos'}, status=400)
    
    try:
        # Primeiro, tentar encontrar o paciente no banco local
        paciente = (
            Paciente.objects
            .annotate(cpf_digits=_cpf_digits_expression('cpf'))
            .filter(cpf_digits=cpf_limpo)
            .first()
        )
        
        if not paciente:
            # Se não encontrou, buscar no e-SUS
            dados_esus = buscar_paciente_esus(cpf_limpo, None)
            
            if dados_esus:
                # Criar novo paciente com dados do e-SUS
                paciente = Paciente.objects.create(
                    nome=dados_esus.get('nome', ''),
                    cpf=cpf_limpo,
                    cns=dados_esus.get('cns', ''),
                    endereco=dados_esus.get('endereco', ''),
                    telefone=dados_esus.get('telefone', ''),
                    data_nascimento=dados_esus.get('data_nascimento'),
                    sexo=dados_esus.get('sexo', ''),
                    nome_mae=dados_esus.get('nome_mae', ''),
                    nome_pai=dados_esus.get('nome_pai', ''),
                    municipio_nascimento=dados_esus.get('municipio_nascimento', ''),
                    nacionalidade=dados_esus.get('nacionalidade', ''),
                    raca_cor=dados_esus.get('raca_cor', ''),
                    escolaridade=dados_esus.get('escolaridade', ''),
                    situacao_familiar=dados_esus.get('situacao_familiar', ''),
                    ocupacao=dados_esus.get('ocupacao', ''),
                )
            else:
                return JsonResponse({'error': 'Paciente não encontrado no sistema local nem no e-SUS'}, status=404)
        else:
            # Se encontrou no banco local, tentar atualizar com dados do e-SUS
            try:
                dados_esus = buscar_paciente_esus(cpf_limpo, None)
                if dados_esus:
                    atualizar_paciente_com_esus(paciente, dados_esus, sobrescrever=False)
                    paciente.save()
            except Exception as e:
                # Se falhar a busca no e-SUS, continuar com os dados locais
                pass
        
        # Retornar dados do paciente
        # Montar endereço completo a partir dos campos estruturados
        endereco_parts = []
        if paciente.logradouro:
            endereco_parts.append(paciente.logradouro)
        if paciente.numero:
            endereco_parts.append(f"nº {paciente.numero}")
        if paciente.bairro:
            endereco_parts.append(paciente.bairro)
        if paciente.cep:
            endereco_parts.append(f"CEP: {paciente.cep}")
        
        endereco_completo = ", ".join(endereco_parts) if endereco_parts else ""
        
        return JsonResponse({
            'success': True,
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome or '',
                'cpf': paciente.cpf or '',
                'cns': paciente.cns or '',
                'endereco': endereco_completo,
                'endereco_completo': endereco_completo,  # Garantir que o endereço completo seja enviado
                'telefone': paciente.telefone or '',
                'data_nascimento': paciente.data_nascimento.strftime('%Y-%m-%d') if paciente.data_nascimento else '',
                'sexo': getattr(paciente, 'sexo', '') or '',  # Campo sexo pode não existir
                'nome_mae': paciente.nome_mae or '',
                'nome_pai': paciente.nome_pai or '',
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def buscar_paciente_por_nome(request):
    """
    AJAX endpoint para buscar pacientes por nome
    """
    nome = request.GET.get('nome', '').strip()
    
    if not nome:
        return JsonResponse({'error': 'Nome é obrigatório'}, status=400)
    
    if len(nome) < 3:
        return JsonResponse({'error': 'Digite pelo menos 3 caracteres'}, status=400)
    
    try:
        # Buscar pacientes no banco local por nome
        pacientes = Paciente.objects.filter(
            nome__icontains=nome
        ).order_by('nome')[:10]  # Limitar a 10 resultados
        
        if not pacientes:
            return JsonResponse({'error': 'Nenhum paciente encontrado com esse nome'}, status=404)
        
        # Preparar lista de pacientes
        pacientes_data = []
        for paciente in pacientes:
            # Montar endereço completo a partir dos campos estruturados
            endereco_parts = []
            if paciente.logradouro:
                endereco_parts.append(paciente.logradouro)
            if paciente.numero:
                endereco_parts.append(f"nº {paciente.numero}")
            if paciente.bairro:
                endereco_parts.append(paciente.bairro)
            if paciente.cep:
                endereco_parts.append(f"CEP: {paciente.cep}")
            endereco_completo = ", ".join(endereco_parts) if endereco_parts else ""
            
            pacientes_data.append({
                'id': paciente.id,
                'nome': paciente.nome or '',
                'cpf': paciente.cpf or '',
                'cns': paciente.cns or '',
                'endereco': endereco_completo,
                'endereco_completo': endereco_completo,
                'telefone': paciente.telefone or '',
                'data_nascimento': paciente.data_nascimento.strftime('%Y-%m-%d') if paciente.data_nascimento else '',
                'sexo': getattr(paciente, 'sexo', '') or '',
                'nome_mae': paciente.nome_mae or '',
                'nome_pai': paciente.nome_pai or '',
            })
        
        return JsonResponse({
            'success': True,
            'pacientes': pacientes_data
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)