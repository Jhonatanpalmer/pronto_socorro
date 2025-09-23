from django import forms
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
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()


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
        super().__init__(*args, **kwargs)
        # Autocomplete-friendly paciente queryset
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


class RegulacaoExameBatchForm(forms.ModelForm):
    """Form usado na tela por paciente para aprovar/agendar múltiplos exames."""
    autorizar = forms.BooleanField(required=False, label='Autorizar')

    class Meta:
        model = RegulacaoExame
        fields = [
            # somente campos a serem atualizados na autorização
            'local_realizacao', 'data_agendada', 'hora_agendada', 'medico_atendente', 'observacoes_regulacao'
        ]
        widgets = {
            'local_realizacao': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'medico_atendente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.cleaned_data.get('autorizar'):
            # exigir campos ao autorizar
            faltando = []
            if not cleaned.get('local_realizacao'):
                faltando.append('Local')
            if not cleaned.get('data_agendada'):
                faltando.append('Data')
            if not cleaned.get('hora_agendada'):
                faltando.append('Hora')
            if not cleaned.get('medico_atendente'):
                faltando.append('Médico Atendente')
            if faltando:
                raise forms.ValidationError(f"Para autorizar, preencha: {', '.join(faltando)}.")
        return cleaned


class RegulacaoConsultaBatchForm(forms.ModelForm):
    """Form usado na tela por paciente para aprovar/agendar múltiplas consultas."""
    autorizar = forms.BooleanField(required=False, label='Autorizar')

    class Meta:
        model = RegulacaoConsulta
        fields = [
            'local_atendimento', 'data_agendada', 'hora_agendada', 'medico_atendente', 'observacoes_regulacao'
        ]
        widgets = {
            'local_atendimento': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'data_agendada': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'hora_agendada': forms.TimeInput(attrs={'class': 'form-control form-control-sm', 'type': 'time'}),
            'medico_atendente': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'observacoes_regulacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.cleaned_data.get('autorizar'):
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
        return cleaned


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