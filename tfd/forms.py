from django import forms
from pacientes.models import Paciente
from viagens.models import DestinoViagem
from .models import TFD


class TFDForm(forms.ModelForm):
    class Meta:
        model = TFD
        fields = [
            'paciente',
            'paciente_nome',
            'paciente_cpf',
            'paciente_cns',
            'paciente_endereco',
            'paciente_telefone',
            'cidade_destino',
            'data_inicio',
            'data_fim',
            'numero_diarias',
            'valor_diaria',
            'valor_beneficio',
            'valor_total',
            'observacoes',
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'paciente_nome': forms.TextInput(attrs={'placeholder': 'Nome do paciente'}),
            'numero_diarias': forms.NumberInput(attrs={'min': '1'}),
            'valor_diaria': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_beneficio': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_total': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'paciente_endereco': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Rua, nº, bairro, cidade', 'maxlength': '300'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # tornar paciente obrigatório no formulário de entrada
        self.fields['paciente'].required = True
        self.fields['data_inicio'].required = True
        self.fields['data_fim'].required = True

        # montar lista de destinos utilizando o catálogo importado
        destinos_qs = DestinoViagem.objects.filter(ativo=True).order_by('nome_cidade', 'uf')
        destino_choices = [('', 'Selecione o destino...')]
        known_values = {choice[0] for choice in destino_choices}
        for destino in destinos_qs:
            value = f"{destino.nome_cidade}/{destino.uf}"
            label = f"{destino.nome_cidade} - {destino.uf}"
            destino_choices.append((value, label))
            known_values.add(value)

        current_value = None
        if self.instance and getattr(self.instance, 'cidade_destino', None):
            current_value = self.instance.cidade_destino
        if self.data:
            current_value = self.data.get(self.add_prefix('cidade_destino')) or current_value
        if current_value and current_value not in known_values:
            destino_choices.append((current_value, current_value))

        original_label = self.fields['cidade_destino'].label
        self.fields['cidade_destino'] = forms.ChoiceField(
            label=original_label,
            choices=destino_choices,
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        if current_value and not self.initial.get('cidade_destino'):
            self.initial['cidade_destino'] = current_value

        # evitar carregar todos; incluir o selecionado (POST/instance) para evitar 'Escolha inválida'
        ids = set()
        posted = self.data.get(self.add_prefix('paciente')) if getattr(self, 'data', None) else None
        if posted and str(posted).isdigit():
            ids.add(int(posted))
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))

        # Se temos IDs, usar o queryset filtrado; caso contrário, permitir todos os pacientes
        # Isso é necessário para que o JavaScript possa selecionar qualquer paciente válido
        if ids:
            self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids)
        else:
            self.fields['paciente'].queryset = Paciente.objects.all()

    def clean_paciente(self):
        """Validação customizada para o campo paciente"""
        paciente = self.cleaned_data.get('paciente')
        
        if not paciente:
            raise forms.ValidationError("É obrigatório selecionar um paciente.")
        
        # Verificar se o paciente existe no banco de dados
        if not Paciente.objects.filter(pk=paciente.pk).exists():
            raise forms.ValidationError("Paciente selecionado não é válido.")
        
        return paciente

    def clean(self):
        cleaned = super().clean()
        from decimal import Decimal

        data_inicio = cleaned.get('data_inicio')
        data_fim = cleaned.get('data_fim')

        if not data_inicio:
            self.add_error('data_inicio', 'Informe a data de início da viagem.')
        if not data_fim:
            self.add_error('data_fim', 'Informe a data de fim da viagem.')

        if data_inicio and data_fim and data_fim < data_inicio:
            self.add_error('data_fim', 'A data de fim não pode ser anterior à data de início.')

        numero = Decimal(cleaned.get('numero_diarias') or 0)
        diaria = Decimal(cleaned.get('valor_diaria') or 0)
        beneficio = Decimal(cleaned.get('valor_beneficio') or 0)

        # recalcular sempre o valor_total para manter consistência
        cleaned['valor_total'] = (diaria * numero) + beneficio

        return cleaned
