from django import forms
from django.db.models import Q
from pacientes.models import Paciente
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame, Especialidade, RegulacaoConsulta, LocalAtendimento, MedicoAmbulatorio, AgendaMedica, AgendaMedicaDia


class UBSForm(forms.ModelForm):
    class Meta:
        model = UBS
        fields = ['nome', 'endereco', 'telefone', 'email', 'responsavel', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MedicoSolicitanteForm(forms.ModelForm):
    class Meta:
        model = MedicoSolicitante
        fields = ['nome', 'crm', 'especialidade', 'telefone', 'email', 'ubs_padrao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'crm': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ubs_padrao': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TipoExameForm(forms.ModelForm):
    class Meta:
        model = TipoExame
        fields = ['nome', 'codigo', 'descricao', 'valor', 'especialidade', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'especialidade': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LocalAtendimentoForm(forms.ModelForm):
    novo_tipo = forms.CharField(required=False, label='Novo tipo', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Informe o novo tipo'}))
    # Sobrescreve o campo para permitir valores fora dos choices fixos, mantendo UI de Select
    tipo = forms.CharField(label='Tipo', widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = LocalAtendimento
        fields = ['nome', 'tipo', 'endereco', 'telefone', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            # 'tipo' é definido acima para não restringir choices
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guardar choices originais do model para manipulação temporária em _post_clean
        self._tipo_field = self._meta.model._meta.get_field('tipo')
        self._tipo_choices_original = list(self._tipo_field.choices or [])

        def _label_for(value, fallback_text=None):
            m = dict(LocalAtendimento.TIPO_CHOICES)
            if value in m:
                return m[value]
            if fallback_text:
                return fallback_text
            return (value or '').replace('_', ' ').title()

        # Monta choices do widget: defaults + tipos do BD
        tipos_presentes = LocalAtendimento.objects.values_list('tipo', flat=True).distinct()
        all_tipos = sorted(set(tipos_presentes) | set(t for t, _ in LocalAtendimento.TIPO_CHOICES))
        choices = [(t, _label_for(t)) for t in all_tipos]

        # Se for POST e o valor postado ainda não estiver na lista, incluir para não dar erro de render
        if self.is_bound:
            posted_tipo = self.data.get(self.add_prefix('tipo'))
            if posted_tipo and posted_tipo not in dict(choices):
                # usar o próprio posted como label humanizada
                choices.append((posted_tipo, _label_for(posted_tipo)))
            # incluir também o slug derivado do novo_tipo, se houver
            posted_novo = (self.data.get(self.add_prefix('novo_tipo')) or '').strip()
            if posted_novo:
                slug = posted_novo.lower().strip().replace(' ', '_')
                slug = ''.join(ch for ch in slug if ch.isalnum() or ch == '_')[:20]
                if slug and slug not in dict(choices):
                    choices.append((slug, _label_for(slug, posted_novo)))

        self.fields['tipo'].widget.choices = choices

    def clean(self):
        cleaned = super().clean()
        # Se for informado um novo tipo, usar ele como valor a ser salvo
        novo = (cleaned.get('novo_tipo') or '').strip()
        if novo:
            slug = novo.lower().strip().replace(' ', '_')
            if len(slug) > 20:
                self.add_error('novo_tipo', 'O identificador do tipo deve ter no máximo 20 caracteres.')
            else:
                cleaned['tipo'] = slug
        return cleaned

    def _post_clean(self):
        """Permite que valores fora dos choices fixos passem na validação de modelo.
        Temporariamente injeta o valor de 'tipo' nos choices do campo do modelo durante full_clean()."""
        # Preparar choices temporários
        valor_tipo = None
        try:
            valor_tipo = (self.cleaned_data.get('tipo') or '').strip()
            novo = (self.cleaned_data.get('novo_tipo') or '').strip()
            if novo:
                # garantir que o slug calculado também é considerado
                s = novo.lower().strip().replace(' ', '_')
                s = ''.join(ch for ch in s if ch.isalnum() or ch == '_')[:20]
                if s:
                    valor_tipo = s
        except Exception:
            pass

        temp_choices = list(self._tipo_choices_original)
        if valor_tipo:
            # usar rótulo humanizado para melhor UX em erros
            label = (valor_tipo or '').replace('_', ' ').title()
            if (valor_tipo, label) not in temp_choices and (valor_tipo, valor_tipo) not in temp_choices:
                temp_choices.append((valor_tipo, label))
        # Injetar choices temporários
        original_ref = self._tipo_field.choices
        self._tipo_field.choices = temp_choices
        try:
            super()._post_clean()
        finally:
            # Restaurar choices originais para não afetar globalmente
            self._tipo_field.choices = original_ref


class MedicoAmbulatorioForm(forms.ModelForm):
    class Meta:
        model = MedicoAmbulatorio
        fields = ['nome', 'crm', 'telefone', 'email', 'ativo', 'especialidades']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'crm': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'especialidades': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        }


class RegulacaoExameForm(forms.ModelForm):
    """Formulário para criar/editar solicitações de exames"""
    class Meta:
        model = RegulacaoExame
        fields = ['paciente', 'ubs_solicitante', 'medico_solicitante', 'tipo_exame', 
                 'justificativa', 'prioridade', 'observacoes_solicitacao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'ubs_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'medico_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'tipo_exame': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_solicitacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Evitar carregar todos os pacientes; permitir o selecionado (POST/instance)
        ids = set()
        # id vindo do POST
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        # id do instance (edição)
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()


class RegulacaoCompletaForm(forms.ModelForm):
    """Formulário completo para edição administrativa de regulações"""
    class Meta:
        model = RegulacaoExame
        fields = ['paciente', 'ubs_solicitante', 'medico_solicitante', 'tipo_exame', 
                 'justificativa', 'prioridade', 'observacoes_solicitacao', 'status', 'regulador', 'motivo_decisao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'ubs_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'medico_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'tipo_exame': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_solicitacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'regulador': forms.Select(attrs={'class': 'form-select'}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class RegulacaoForm(forms.ModelForm):
    """Formulário para fazer a regulação (autorizar/negar)"""
    class Meta:
        model = RegulacaoExame
        fields = ['status', 'motivo_decisao', 'local_realizacao', 'data_agendada', 'observacoes_regulacao']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'local_realizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas status relevantes para regulação
        self.fields['status'].choices = [
            ('autorizado', 'Autorizado'),
            ('negado', 'Negado'),
        ]
        # UX: impedir escolha de datas passadas no input (validação real é no clean)
        try:
            from django.utils import timezone
            self.fields['data_agendada'].widget.attrs['min'] = timezone.localdate().isoformat()
        except Exception:
            pass

    def clean(self):
        cleaned = super().clean()
        # Se for autorizar, garantir que a data não é passada
        status = cleaned.get('status')
        data = cleaned.get('data_agendada')
        if status == 'autorizado' and data:
            from django.utils import timezone
            hoje = timezone.localdate()
            if data < hoje:
                self.add_error('data_agendada', 'A data do agendamento deve ser hoje ou futura.')
        return cleaned


class EspecialidadeForm(forms.ModelForm):
    # Campos opcionais para cadastrar rapidamente um médico do ambulatório vinculado a esta especialidade
    novo_medico_nome = forms.CharField(label='Nome do médico (ambulatório)', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: João da Silva'}))
    novo_medico_crm = forms.CharField(label='CRM do médico', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: 123456'}))
    # Vínculo N:1 Especialidade -> N Médicos (Ambulatório)
    medicos = forms.ModelMultipleChoiceField(
        label='Médicos do ambulatório',
        required=False,
        queryset=MedicoAmbulatorio.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
        help_text='Selecione um ou mais médicos que atendem esta especialidade.'
    )
    class Meta:
        model = Especialidade
        fields = ['nome', 'descricao', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Popular queryset dos médicos ativos e ordenar por nome
        self.fields['medicos'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        # Inicial: médicos já vinculados a esta especialidade
        if getattr(self.instance, 'pk', None):
            self.fields['medicos'].initial = list(self.instance.medicos_ambulatorio.values_list('pk', flat=True))

    def save(self, commit=True):
        espec = super().save(commit=commit)
        # Se preenchidos, criar médico do ambulatório e vincular a esta especialidade
        nome = (self.cleaned_data.get('novo_medico_nome') or '').strip()
        crm = (self.cleaned_data.get('novo_medico_crm') or '').strip()
        if nome and crm:
            try:
                med, _ = MedicoAmbulatorio.objects.get_or_create(crm=crm, defaults={'nome': nome, 'ativo': True})
                if not med.especialidades.filter(pk=espec.pk).exists():
                    med.especialidades.add(espec)
            except Exception:
                pass
        # Sincronizar seleção de médicos do formulário com a M2M da especialidade
        try:
            selecionados = list(self.cleaned_data.get('medicos') or [])
            if commit:
                espec.medicos_ambulatorio.set(selecionados)
            else:
                # Se commit=False, deferimos a chamada; o caller deve gerenciar M2M
                self._pending_medicos = selecionados
        except Exception:
            pass
        return espec


class RegulacaoConsultaForm(forms.ModelForm):
    class Meta:
        model = RegulacaoConsulta
        fields = ['paciente', 'ubs_solicitante', 'medico_solicitante', 'especialidade',
                  'justificativa', 'prioridade', 'observacoes_solicitacao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'ubs_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'medico_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'especialidade': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_solicitacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Evitar carregar todos os pacientes; permitir o selecionado (POST/instance)
        ids = set()
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        # Se vier via GET e o form não está bound, pré-selecionar paciente
        if not self.is_bound and self.request and getattr(self.request, 'method', 'GET') == 'GET':
            try:
                pid = int(self.request.GET.get('paciente') or 0)
                if pid:
                    ids.add(pid)
                    self.fields['paciente'].initial = pid
            except (TypeError, ValueError):
                pass
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()

        # Se usuário for UBS, restringir ubs_solicitante e médico
        user = getattr(self.request, 'user', None)
        ubs = getattr(getattr(user, 'perfil_ubs', None), 'ubs', None)
        if ubs:
            self.fields['ubs_solicitante'].queryset = UBS.objects.filter(pk=ubs.pk)
            self.fields['ubs_solicitante'].initial = ubs
            self.fields['medico_solicitante'].queryset = MedicoSolicitante.objects.filter(ubs_padrao=ubs, ativo=True).order_by('nome')
        # Pré-selecionar especialidade via GET (?especialidade=ID)
        if not self.is_bound and self.request and getattr(self.request, 'method', 'GET') == 'GET':
            try:
                eid = int(self.request.GET.get('especialidade') or 0)
                if eid:
                    self.fields['especialidade'].initial = eid
            except (TypeError, ValueError):
                pass

    def clean(self):
        cleaned = super().clean()
        # Regras UBS: ubs obrigatoriamente igual do usuário e médico da mesma UBS
        user = getattr(getattr(self, 'request', None), 'user', None)
        ubs_user = getattr(getattr(user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            ubs_solic = cleaned.get('ubs_solicitante')
            med = cleaned.get('medico_solicitante')
            if ubs_solic and ubs_solic.pk != ubs_user.pk:
                self.add_error('ubs_solicitante', 'UBS deve ser a sua unidade.')
            if med and med.ubs_padrao_id != ubs_user.pk:
                self.add_error('medico_solicitante', 'Escolha um médico vinculado à sua UBS.')
        paciente = cleaned.get('paciente')
        especialidade = cleaned.get('especialidade')
        if paciente and especialidade:
            # Bloquear se já existe em fila, ou autorizado com data futura/indefinida.
            from django.utils import timezone
            hoje = timezone.localdate()
            qs = RegulacaoConsulta.objects.filter(
                paciente=paciente,
                especialidade=especialidade,
            ).filter(
                Q(status='fila') |
                (Q(status='autorizado') & (Q(data_agendada__isnull=True) | Q(data_agendada__gte=hoje)))
            )
            # Em edição, ignorar o próprio registro
            if getattr(self.instance, 'pk', None):
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                # Construir mensagem indicando os status encontrados
                statuses = sorted(set(qs.values_list('status', flat=True)))
                self.add_error('especialidade', forms.ValidationError(
                    f"Paciente já possui uma solicitação para esta especialidade com status: {', '.join(statuses)}. Conclua ou cancele antes de criar outra.")
                )
        return cleaned


class RegulacaoConsultaCompletaForm(forms.ModelForm):
    class Meta:
        model = RegulacaoConsulta
        fields = ['paciente', 'ubs_solicitante', 'medico_solicitante', 'especialidade',
                  'justificativa', 'prioridade', 'observacoes_solicitacao',
                  'status', 'regulador', 'motivo_decisao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'ubs_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'medico_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'especialidade': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_solicitacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'regulador': forms.Select(attrs={'class': 'form-select'}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ids = set()
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()


class RegulacaoExameCreateForm(forms.ModelForm):
    """Formulário de criação com múltiplos exames no mesmo pedido."""
    tipos_exame = forms.ModelMultipleChoiceField(
        label='Tipos de Exame',
        queryset=TipoExame.objects.filter(ativo=True).order_by('nome'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
        required=True,
        help_text='Segure Ctrl (ou Cmd) para selecionar mais de um.'
    )

    class Meta:
        model = RegulacaoExame
        fields = ['paciente', 'ubs_solicitante', 'medico_solicitante',
                  'justificativa', 'prioridade', 'observacoes_solicitacao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-select'}),
            'ubs_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'medico_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes_solicitacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Autocomplete-friendly paciente queryset
        ids = set()
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        # Se vier via GET e o form não está bound, pré-selecionar paciente
        if not self.is_bound and self.request and getattr(self.request, 'method', 'GET') == 'GET':
            try:
                pid = int(self.request.GET.get('paciente') or 0)
                if pid:
                    ids.add(pid)
                    self.fields['paciente'].initial = pid
            except (TypeError, ValueError):
                pass
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()

        # Se usuário for UBS, restringir ubs_solicitante e médico
        user = getattr(self.request, 'user', None)
        ubs = getattr(getattr(user, 'perfil_ubs', None), 'ubs', None)
        if ubs:
            self.fields['ubs_solicitante'].queryset = UBS.objects.filter(pk=ubs.pk)
            self.fields['ubs_solicitante'].initial = ubs
            self.fields['medico_solicitante'].queryset = MedicoSolicitante.objects.filter(ubs_padrao=ubs, ativo=True).order_by('nome')

        # Pré-selecionar tipos de exame via GET (?tipos=1,2,3) quando não for POST
        if not self.is_bound and self.request and getattr(self.request, 'method', 'GET') == 'GET':
            tipos_param = (self.request.GET.get('tipos') or '').strip()
            pre_ids = []
            if tipos_param:
                for part in tipos_param.split(','):
                    try:
                        pre_ids.append(int(part))
                    except (TypeError, ValueError):
                        continue
            if pre_ids:
                self.fields['tipos_exame'].initial = pre_ids

    def clean(self):
        cleaned = super().clean()
        # Regras UBS: ubs obrigatoriamente igual do usuário e médico da mesma UBS
        user = getattr(getattr(self, 'request', None), 'user', None)
        ubs_user = getattr(getattr(user, 'perfil_ubs', None), 'ubs', None)
        if ubs_user:
            ubs_solic = cleaned.get('ubs_solicitante')
            med = cleaned.get('medico_solicitante')
            if ubs_solic and ubs_solic.pk != ubs_user.pk:
                self.add_error('ubs_solicitante', 'UBS deve ser a sua unidade.')
            if med and med.ubs_padrao_id != ubs_user.pk:
                self.add_error('medico_solicitante', 'Escolha um médico vinculado à sua UBS.')
        return cleaned



class RegulacaoExameBatchForm(forms.ModelForm):
    """Form usado na tela por paciente para aprovar/agendar múltiplos exames."""
    autorizar = forms.BooleanField(required=False, label='Autorizar')
    negar = forms.BooleanField(required=False, label='Negar')
    pendenciar = forms.BooleanField(required=False, label='Pendenciar')
    pendencia_motivo = forms.CharField(required=False, label='Motivo da pendência', widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o que falta/pendência para a UBS resolver'}))

    # Filtro auxiliar (não salvo): tipo do local para filtrar opções de Local nos Exames
    local_tipo = forms.ChoiceField(required=False, label='Tipo do Local', choices=(), widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))

    class Meta:
        model = RegulacaoExame
        fields = [
            # somente campos a serem atualizados na autorização
            'local_realizacao', 'data_agendada', 'hora_agendada', 'medico_atendente', 'observacoes_regulacao',
            'motivo_decisao', 'pendencia_motivo',
        ]
        widgets = {
            'local_realizacao': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'medico_atendente': forms.Select(attrs={'class': 'form-select form-select-sm ex-medico'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o motivo da negação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carregar locais de atendimento como opções para exames também
        locais = LocalAtendimento.objects.filter(ativo=True).order_by('nome')
        self.fields['local_realizacao'].choices = [('', '— Selecione —')] + [(loc.nome, loc.nome) for loc in locais]
        # Carregar tipos existentes dinamicamente a partir dos locais cadastrados
        tipo_label_map = dict(LocalAtendimento.TIPO_CHOICES)
        tipos_presentes = (
            LocalAtendimento.objects.filter(ativo=True)
            .values_list('tipo', flat=True)
            .distinct()
        )
        tipo_choices = [('', '— Tipo —')] + [
            (t, tipo_label_map.get(t, t.replace('_', ' ').title())) for t in sorted(tipos_presentes)
        ]
        self.fields['local_tipo'].choices = tipo_choices
        # UX: impedir escolha de datas passadas no input (validação real é no clean)
        try:
            from django.utils import timezone
            self.fields['data_agendada'].widget.attrs['min'] = timezone.localdate().isoformat()
        except Exception:
            pass
        # Médicos sugeridos conforme especialidade vinculada ao tipo de exame
        medico_field = self.fields['medico_atendente']
        medico_qs = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        tipo = getattr(self.instance, 'tipo_exame', None)
        espec = getattr(tipo, 'especialidade', None)
        if espec:
            medico_qs = medico_qs.filter(especialidades=espec).distinct()
        medico_field.queryset = medico_qs
        medico_field.empty_label = '— Selecione —'

    def clean(self):
        cleaned = super().clean()
        autorizar = self.cleaned_data.get('autorizar')
        negar = self.cleaned_data.get('negar')

        pendenciar = self.cleaned_data.get('pendenciar')
        # Não permitir marcar ações conflitantes
        actions = [bool(autorizar), bool(negar), bool(pendenciar)]
        if sum(1 for a in actions if a) > 1:
            raise forms.ValidationError('Selecione apenas uma ação: Autorizar, Negar ou Pendenciar.')

        if autorizar:
            # Nesta tela, exigimos apenas Data e Hora; o Local será definido no fluxo posterior
            faltando = []
            if not cleaned.get('data_agendada'):
                faltando.append('Data')
            if not cleaned.get('hora_agendada'):
                faltando.append('Hora')
            if not cleaned.get('medico_atendente'):
                faltando.append('Médico Atendente')
            if faltando:
                raise forms.ValidationError(f"Para autorizar, preencha: {', '.join(faltando)}.")
            # Não permitir datas passadas
            from django.utils import timezone
            hoje = timezone.localdate()
            data = cleaned.get('data_agendada')
            if data and data < hoje:
                self.add_error('data_agendada', 'A data do agendamento deve ser hoje ou futura.')
            # Validar disponibilidade da agenda do médico
            medico = cleaned.get('medico_atendente')
            tipo = getattr(self.instance, 'tipo_exame', None)
            espec = getattr(tipo, 'especialidade', None)
            if medico and data and espec:
                usados_exames = RegulacaoExame.objects.filter(
                    medico_atendente=medico,
                    data_agendada=data,
                    status='autorizado'
                ).exclude(pk=self.instance.pk).count()
                usados_consultas = RegulacaoConsulta.objects.filter(
                    medico_atendente=medico,
                    data_agendada=data,
                    status='autorizado'
                ).count()
                agenda_dia = AgendaMedicaDia.objects.filter(
                    medico=medico,
                    especialidade=espec,
                    data=data,
                    ativo=True,
                ).first()
                if not agenda_dia:
                    raise forms.ValidationError('Não há agenda cadastrada para este médico nesta data (agenda do dia).')
                capacidade = agenda_dia.capacidade or 0
                if usados_exames + usados_consultas >= capacidade:
                    raise forms.ValidationError('Não há vagas disponíveis para este médico nesta data (agenda do dia).')
        if negar:
            # exigir motivo ao negar
            if not (cleaned.get('motivo_decisao') or '').strip():
                raise forms.ValidationError('Para negar, informe o motivo da decisão.')
        if pendenciar:
            # Permitir que o motivo venha já salvo no registro (via tela "Editar pendência").
            motivo = (cleaned.get('pendencia_motivo') or '').strip()
            if not motivo:
                motivo = (getattr(self.instance, 'pendencia_motivo', '') or '').strip()
            if not motivo:
                raise forms.ValidationError('Para pendenciar, informe o motivo da pendência.')
            # Propagar para cleaned_data para uso no salvamento
            cleaned['pendencia_motivo'] = motivo
        return cleaned

    def apply_regulacao_role(self):
        # Sem diferenciação: ambos os perfis podem agendar; manter campos habilitados
        return None


class RegulacaoConsultaBatchForm(forms.ModelForm):
    """Form usado na tela por paciente para aprovar/agendar múltiplas consultas."""
    autorizar = forms.BooleanField(required=False, label='Autorizar')
    negar = forms.BooleanField(required=False, label='Negar')
    pendenciar = forms.BooleanField(required=False, label='Pendenciar')
    pendencia_motivo = forms.CharField(required=False, label='Motivo da pendência', widget=forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o que falta/pendência para a UBS resolver'}))
    # Filtro auxiliar (não é salvo no modelo): seleciona o tipo e filtra os locais
    local_tipo = forms.ChoiceField(required=False, label='Tipo do Local', choices=(), widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))

    class Meta:
        model = RegulacaoConsulta
        fields = [
            'local_atendimento', 'data_agendada', 'hora_agendada', 'medico_atendente', 'observacoes_regulacao',
            'motivo_decisao', 'pendencia_motivo',
        ]
        widgets = {
            'local_atendimento': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'medico_atendente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o motivo da negação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carregar locais de atendimento como opções
        locais = LocalAtendimento.objects.filter(ativo=True).order_by('nome')
        self.fields['local_atendimento'].choices = [('', '— Selecione —')] + [(loc.nome, loc.nome) for loc in locais]
        # Carregar tipos existentes dinamicamente a partir dos locais cadastrados
        tipo_label_map = dict(LocalAtendimento.TIPO_CHOICES)
        tipos_presentes = (
            LocalAtendimento.objects.filter(ativo=True)
            .values_list('tipo', flat=True)
            .distinct()
        )
        tipo_choices = [('', '— Tipo —')] + [
            (t, tipo_label_map.get(t, t.replace('_', ' ').title())) for t in sorted(tipos_presentes)
        ]
        self.fields['local_tipo'].choices = tipo_choices
        # UX: impedir escolha de datas passadas no input (validação real é no clean)
        try:
            from django.utils import timezone
            self.fields['data_agendada'].widget.attrs['min'] = timezone.localdate().isoformat()
        except Exception:
            pass
        # Se houver especialidade definida na instância, filtrar médicos do ambulatório correspondentes
        espec = getattr(self.instance, 'especialidade', None)
        if 'medico_atendente' in self.fields:
            if espec is not None:
                self.fields['medico_atendente'].queryset = MedicoAmbulatorio.objects.filter(ativo=True, especialidades=espec).order_by('nome')
            else:
                self.fields['medico_atendente'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')

    def clean(self):
        cleaned = super().clean()
        autorizar = self.cleaned_data.get('autorizar')
        negar = self.cleaned_data.get('negar')

        pendenciar = self.cleaned_data.get('pendenciar')
        # Não permitir marcar ações conflitantes
        actions = [bool(autorizar), bool(negar), bool(pendenciar)]
        if sum(1 for a in actions if a) > 1:
            raise forms.ValidationError('Selecione apenas uma ação: Autorizar, Negar ou Pendenciar.')

        if autorizar:
            # Nesta tela, exigimos Data, Hora e Médico; o Local será definido no fluxo posterior
            faltando = []
            if not cleaned.get('data_agendada'):
                faltando.append('Data')
            if not cleaned.get('hora_agendada'):
                faltando.append('Hora')
            if not cleaned.get('medico_atendente'):
                faltando.append('Médico Atendente')
            if faltando:
                raise forms.ValidationError(f"Para autorizar, preencha: {', '.join(faltando)}.")
            # Validar agenda médica (mensal/por dia): deve existir agenda para a data e ter vaga
            medico = cleaned.get('medico_atendente')
            data = cleaned.get('data_agendada')
            espec = getattr(self.instance, 'especialidade', None)
            if medico and data and espec:
                usados = RegulacaoConsulta.objects.filter(
                    medico_atendente=medico,
                    data_agendada=data,
                    status='autorizado'
                ).count()
                agenda_dia = AgendaMedicaDia.objects.filter(medico=medico, especialidade=espec, data=data, ativo=True).first()
                if not agenda_dia:
                    raise forms.ValidationError('Não há agenda cadastrada para este médico nesta data (agenda do dia).')
                if usados >= (agenda_dia.capacidade or 0):
                    raise forms.ValidationError('Não há vagas disponíveis para este médico nesta data (agenda do dia).')
            # Não permitir datas passadas
            from django.utils import timezone
            hoje = timezone.localdate()
            if data and data < hoje:
                self.add_error('data_agendada', 'A data do agendamento deve ser hoje ou futura.')
        if negar:
            if not (cleaned.get('motivo_decisao') or '').strip():
                raise forms.ValidationError('Para negar, informe o motivo da decisão.')
        if pendenciar:
            # Permitir que o motivo venha já salvo no registro (via tela "Editar pendência").
            motivo = (cleaned.get('pendencia_motivo') or '').strip()
            if not motivo:
                motivo = (getattr(self.instance, 'pendencia_motivo', '') or '').strip()
            if not motivo:
                raise forms.ValidationError('Para pendenciar, informe o motivo da pendência.')
            cleaned['pendencia_motivo'] = motivo
        return cleaned

    def apply_regulacao_role(self):
        # Sem diferenciação: ambos os perfis podem agendar; manter campos habilitados
        return None


class SIGTAPImportForm(forms.Form):
    arquivo = forms.FileField(label='Arquivo SIGTAP (.rar ou .zip)', help_text='Envie o pacote do SIGTAP contendo tb_procedimento (.csv/.txt) e opcional tb_procedimento_valor.')
    only_groups = forms.CharField(label='Apenas grupos (CO_GRUPO)', required=False, help_text='Ex: 04,05,06,07')
    name_contains = forms.CharField(label='Nome contém (NO_PROCEDIMENTO)', required=False, help_text='Termos separados por vírgula. Ex: EXAME,LAB,IMAGEM')
    set_valor = forms.BooleanField(label='Importar valores (SH+SA+SP)', required=False, initial=False)
    encoding = forms.CharField(label='Encoding', required=False, initial='latin-1', help_text='Padrão: latin-1')

    def clean_arquivo(self):
        f = self.cleaned_data['arquivo']
        name = (f.name or '').lower()
        if not (name.endswith('.rar') or name.endswith('.zip')):
            raise forms.ValidationError('Envie um arquivo .rar ou .zip.')
        return f


# ====== Forms de edição rápida de textos (Obs / Motivo / Pendência) ======

class RegulacaoExameTextosForm(forms.ModelForm):
    class Meta:
        model = RegulacaoExame
        fields = ['observacoes_regulacao', 'motivo_decisao', 'pendencia_motivo']
        widgets = {
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Observações gerais sobre o agendamento/autorização'}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Obrigatório quando negar: descreva o motivo da negativa'}),
            'pendencia_motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Obrigatório quando pendenciar: descreva claramente o que falta para a UBS'}),
        }


class RegulacaoConsultaTextosForm(forms.ModelForm):
    class Meta:
        model = RegulacaoConsulta
        fields = ['observacoes_regulacao', 'motivo_decisao', 'pendencia_motivo']
        widgets = {
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Observações gerais sobre o agendamento/autorização'}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Obrigatório quando negar: descreva o motivo da negativa'}),
            'pendencia_motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Obrigatório quando pendenciar: descreva claramente o que falta para a UBS'}),
        }


class AgendaMedicaForm(forms.ModelForm):
    class Meta:
        model = AgendaMedica
        fields = ['medico', 'especialidade', 'dia_semana', 'capacidade', 'ativo']
        widgets = {
            'medico': forms.Select(attrs={'class': 'form-select'}),
            'especialidade': forms.Select(attrs={'class': 'form-select'}),
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Somente médicos e especialidades ativas por padrão
        self.fields['medico'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        self.fields['especialidade'].queryset = Especialidade.objects.filter(ativa=True).order_by('nome')

    def clean(self):
        cleaned = super().clean()
        med = cleaned.get('medico')
        espec = cleaned.get('especialidade')
        if med and espec:
            # Garantir que o médico está vinculado à especialidade selecionada
            if not med.especialidades.filter(pk=espec.pk).exists():
                self.add_error('especialidade', 'O médico selecionado não está vinculado a esta especialidade. Vá em Especialidades para vinculá-lo, ou ajuste aqui a especialidade.')
        return cleaned


class AgendaMedicaDiaForm(forms.ModelForm):
    class Meta:
        model = AgendaMedicaDia
        fields = ['medico', 'especialidade', 'data', 'capacidade', 'ativo']
        widgets = {
            'medico': forms.Select(attrs={'class': 'form-select'}),
            'especialidade': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medico'].queryset = MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome')
        self.fields['especialidade'].queryset = Especialidade.objects.filter(ativa=True).order_by('nome')

    def clean(self):
        cleaned = super().clean()
        med = cleaned.get('medico')
        espec = cleaned.get('especialidade')
        if med and espec and not med.especialidades.filter(pk=espec.pk).exists():
            self.add_error('especialidade', 'O médico selecionado não está vinculado a esta especialidade.')
        return cleaned


class AgendaMensalGerarForm(forms.Form):
    medico = forms.ModelChoiceField(queryset=MedicoAmbulatorio.objects.filter(ativo=True).order_by('nome'), label='Médico', widget=forms.Select(attrs={'class': 'form-select'}))
    especialidade = forms.ModelChoiceField(queryset=Especialidade.objects.filter(ativa=True).order_by('nome'), label='Especialidade', widget=forms.Select(attrs={'class': 'form-select'}))
    inicio = forms.DateField(label='Início', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    meses = forms.IntegerField(label='Meses a gerar', min_value=1, max_value=6, initial=6, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    dias_semana = forms.MultipleChoiceField(label='Dias da semana', choices=AgendaMedica.DIA_SEMANA_CHOICES, widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 7}))
    capacidade = forms.IntegerField(label='Capacidade por dia', min_value=0, initial=10, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    sobrescrever = forms.BooleanField(label='Sobrescrever dias já existentes', required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))