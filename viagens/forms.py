from django import forms
from .models import Viagem, TipoAtendimentoViagem, HospitalAtendimento, DestinoViagem
from motorista.models import Motorista
from pacientes.models import Paciente
from django.core.exceptions import ValidationError
import datetime

class ViagemForm(forms.ModelForm):
    class Meta:
        model = Viagem
        fields = [
            'paciente', 'endereco_paciente', 'destino', 'data_viagem', 'hora_saida',
            'veiculo', 'motorista', 'hospital', 'tipo_atendimento', 'acompanhante',
            'observacoes'
        ]

        widgets = {
            'data_viagem': forms.DateInput(attrs={'type': 'date'}),
        }

        error_messages = {
            'data_viagem': {
                'invalid': 'Informe uma data válida.',
                'required': 'Informe a data da viagem.',
            }
        }

    def __init__(self, *args, **kwargs):
        super(ViagemForm, self).__init__(*args, **kwargs)

        # Evitar carregar 40k+ opções; incluir paciente selecionado (POST/instance) para evitar 'Escolha inválida'
        ids = set()
        # permitir que a view injete initial['paciente'] (ex.: via ?paciente=ID)
        try:
            init_pid = self.initial.get('paciente')
            if init_pid:
                ids.add(int(init_pid))
        except (ValueError, TypeError, AttributeError):
            pass
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        paciente_field = self.fields['paciente']
        queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()
        paciente_field.queryset = queryset

        selected_id = None
        if posted:
            try:
                selected_id = int(posted)
            except (TypeError, ValueError):
                selected_id = None
        if not selected_id and init_pid:
            try:
                selected_id = int(init_pid)
            except (TypeError, ValueError):
                selected_id = None
        if not selected_id and getattr(self.instance, 'paciente_id', None):
            selected_id = int(self.instance.paciente_id)

        pacientes_cache = {p.pk: p for p in queryset}
        selected = pacientes_cache.get(selected_id)

        if selected:
            endereco_partes = []
            if getattr(selected, 'logradouro', None):
                endereco_partes.append(selected.logradouro)
            if getattr(selected, 'numero', None):
                endereco_partes.append(f"nº {selected.numero}")
            if getattr(selected, 'bairro', None):
                endereco_partes.append(selected.bairro)
            if getattr(selected, 'cep', None):
                endereco_partes.append(f"CEP: {selected.cep}")
            endereco_inicial = ", ".join(endereco_partes)
        else:
            endereco_inicial = ''

        attrs = {
            'data-selected-name': selected.nome if selected else '',
            'data-selected-cpf': selected.cpf if selected and getattr(selected, 'cpf', None) else '',
            'data-selected-telefone': selected.telefone if selected and getattr(selected, 'telefone', None) else '',
            'data-selected-endereco': endereco_inicial,
        }
        paciente_field.widget = forms.HiddenInput(attrs=attrs)
        if selected_id:
            paciente_field.initial = selected_id

        # Ajustar lista de cidades de destino
        destinos_qs = DestinoViagem.objects.filter(ativo=True).order_by('nome_cidade', 'uf')
        destino_choices = [('', 'Selecione...')] + [
            (f"{d.nome_cidade}/{d.uf}", f"{d.nome_cidade}/{d.uf}") for d in destinos_qs
        ]
        current_destino = (self.initial.get('destino') or getattr(self.instance, 'destino', '') or '').strip()
        posted_destino = ''
        if hasattr(self, 'data'):
            posted_destino = (self.data.get(self.add_prefix('destino')) or '').strip()
        if posted_destino and posted_destino not in {value for value, _ in destino_choices if value}:
            destino_choices.append((posted_destino, f"{posted_destino} (não cadastrado)"))
        elif current_destino and current_destino not in {value for value, _ in destino_choices if value}:
            destino_choices.append((current_destino, f"{current_destino} (inativo)"))
        self.fields['destino'].widget = forms.Select(choices=destino_choices)
        self.fields['destino'].label = 'Cidade de Destino'

        # Ajustando exibição de hora de saída (30 em 30 minutos)
        if hasattr(self.instance, 'hora_saida'):
            self.fields['hora_saida'].widget = forms.Select(choices=self.instance._meta.get_field('hora_saida').choices)
        else:
            self.fields['hora_saida'].widget = forms.Select(choices=[])

        # Popular motorista com todos cadastrados (pode ser grande, mas funcional)
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome_completo')

        # Tipos de atendimento disponíveis (lista dinâmica)
        tipos_qs = TipoAtendimentoViagem.objects.filter(ativo=True).order_by('nome')
        tipo_choices = [('', 'Selecione...')] + [(t.nome, t.nome) for t in tipos_qs]
        current_tipo = self.initial.get('tipo_atendimento') or getattr(self.instance, 'tipo_atendimento', '')
        if current_tipo and current_tipo not in {value for value, _ in tipo_choices if value}:
            tipo_choices.append((current_tipo, f"{current_tipo} (inativo)"))
        if 'Não informado' not in {value for value, _ in tipo_choices}:
            tipo_choices.append(('Não informado', 'Não informado'))
        self.fields['tipo_atendimento'].widget = forms.Select(choices=tipo_choices)
        self.fields['tipo_atendimento'].required = False

        # Hospitais de atendimento disponíveis
        hospitais_qs = HospitalAtendimento.objects.filter(ativo=True).order_by('nome')
        hospital_choices = [('', 'Selecione...')] + [(h.nome, h.nome) for h in hospitais_qs]
        current_hospital = self.initial.get('hospital') or getattr(self.instance, 'hospital', '')
        if current_hospital and current_hospital not in {value for value, _ in hospital_choices if value}:
            hospital_choices.append((current_hospital, f"{current_hospital} (inativo)"))
        if 'Não informado' not in {value for value, _ in hospital_choices}:
            hospital_choices.append(('Não informado', 'Não informado'))
        self.fields['hospital'].widget = forms.Select(choices=hospital_choices)
        self.fields['hospital'].required = False

        # Evitar selecionar datas anteriores no input (navegador)
        hoje = datetime.date.today().isoformat()
        if 'data_viagem' in self.fields:
            self.fields['data_viagem'].widget.attrs.update({'min': hoje})

    def clean_data_viagem(self):
        data = self.cleaned_data.get('data_viagem')
        if data:
            hoje = datetime.date.today()
            if data < hoje:
                raise ValidationError('A data da viagem não pode ser anterior à data de hoje.')
        return data

    def clean_tipo_atendimento(self):
        valor = (self.cleaned_data.get('tipo_atendimento') or '').strip()
        return valor or 'Não informado'

    def clean_hospital(self):
        valor = (self.cleaned_data.get('hospital') or '').strip()
        return valor or 'Não informado'

    def clean_destino(self):
        valor = (self.cleaned_data.get('destino') or '').strip()
        if not valor:
            raise ValidationError('Selecione a cidade de destino.')
        return valor


class TipoAtendimentoViagemForm(forms.ModelForm):
    class Meta:
        model = TipoAtendimentoViagem
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex.: Consulta, Exame'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Descrição opcional'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class HospitalAtendimentoForm(forms.ModelForm):
    class Meta:
        model = HospitalAtendimento
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Nome do hospital ou clínica'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Observação opcional'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DestinoViagemForm(forms.ModelForm):
    class Meta:
        model = DestinoViagem
        fields = ['nome_cidade', 'uf', 'ativo']
        widgets = {
            'nome_cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Uberaba'}),
            'uf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_uf(self):
        uf = (self.cleaned_data.get('uf') or '').strip().upper()
        if len(uf) != 2:
            raise ValidationError('Informe a UF com 2 letras.')
        return uf

