from django import forms
from django.db.models import Q
from pacientes.models import Paciente
from .models import UBS, MedicoSolicitante, TipoExame, RegulacaoExame, Especialidade, RegulacaoConsulta


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
        fields = ['nome', 'codigo', 'descricao', 'valor', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
    class Meta:
        model = Especialidade
        fields = ['nome', 'descricao', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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

    class Meta:
        model = RegulacaoExame
        fields = [
            # somente campos a serem atualizados na autorização
            'local_realizacao', 'data_agendada', 'hora_agendada', 'observacoes_regulacao',
            'motivo_decisao',
        ]
        widgets = {
            'local_realizacao': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o motivo da negação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UX: impedir escolha de datas passadas no input (validação real é no clean)
        try:
            from django.utils import timezone
            self.fields['data_agendada'].widget.attrs['min'] = timezone.localdate().isoformat()
        except Exception:
            pass

    def clean(self):
        cleaned = super().clean()
        autorizar = self.cleaned_data.get('autorizar')
        negar = self.cleaned_data.get('negar')

        # Não permitir marcar autorizar e negar ao mesmo tempo
        if autorizar and negar:
            raise forms.ValidationError('Selecione apenas uma ação: Autorizar ou Negar.')

        if autorizar:
            # exigir campos ao autorizar para todos os perfis
            faltando = []
            if not cleaned.get('local_realizacao'):
                faltando.append('Local')
            if not cleaned.get('data_agendada'):
                faltando.append('Data')
            if not cleaned.get('hora_agendada'):
                faltando.append('Hora')
            if faltando:
                raise forms.ValidationError(f"Para autorizar, preencha: {', '.join(faltando)}.")
            # Não permitir datas passadas
            from django.utils import timezone
            hoje = timezone.localdate()
            data = cleaned.get('data_agendada')
            if data and data < hoje:
                self.add_error('data_agendada', 'A data do agendamento deve ser hoje ou futura.')
        if negar:
            # exigir motivo ao negar
            if not (cleaned.get('motivo_decisao') or '').strip():
                raise forms.ValidationError('Para negar, informe o motivo da decisão.')
        return cleaned

    def apply_regulacao_role(self):
        # Sem diferenciação: ambos os perfis podem agendar; manter campos habilitados
        return None


class RegulacaoConsultaBatchForm(forms.ModelForm):
    """Form usado na tela por paciente para aprovar/agendar múltiplas consultas."""
    autorizar = forms.BooleanField(required=False, label='Autorizar')
    negar = forms.BooleanField(required=False, label='Negar')

    class Meta:
        model = RegulacaoConsulta
        fields = [
            'local_atendimento', 'data_agendada', 'hora_agendada', 'medico_atendente', 'observacoes_regulacao',
            'motivo_decisao',
        ]
        widgets = {
            'local_atendimento': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'medico_atendente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'motivo_decisao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2, 'placeholder': 'Descreva o motivo da negação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UX: impedir escolha de datas passadas no input (validação real é no clean)
        try:
            from django.utils import timezone
            self.fields['data_agendada'].widget.attrs['min'] = timezone.localdate().isoformat()
        except Exception:
            pass

    def clean(self):
        cleaned = super().clean()
        autorizar = self.cleaned_data.get('autorizar')
        negar = self.cleaned_data.get('negar')

        # Não permitir marcar autorizar e negar ao mesmo tempo
        if autorizar and negar:
            raise forms.ValidationError('Selecione apenas uma ação: Autorizar ou Negar.')

        if autorizar:
            faltando = []
            if not cleaned.get('local_atendimento'):
                faltando.append('Local')
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
        if negar:
            if not (cleaned.get('motivo_decisao') or '').strip():
                raise forms.ValidationError('Para negar, informe o motivo da decisão.')
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