from django import forms
from pacientes.models import Paciente
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
            'paciente_nome': forms.TextInput(attrs={'placeholder': 'Acompanhante (se houver)'}),
            'numero_diarias': forms.NumberInput(attrs={'min': '1'}),
            'valor_diaria': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_beneficio': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_total': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cidade_destino': forms.TextInput(attrs={'placeholder': 'Cidade de destino'}),
            'paciente_endereco': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Rua, nº, bairro, cidade', 'maxlength': '300'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # tornar paciente obrigatório no formulário de entrada
        self.fields['paciente'].required = True
        # evitar carregar todos; incluir o selecionado (POST/instance) para evitar 'Escolha inválida'
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

    def clean(self):
        cleaned = super().clean()
        from decimal import Decimal

        numero = Decimal(cleaned.get('numero_diarias') or 0)
        diaria = Decimal(cleaned.get('valor_diaria') or 0)
        beneficio = Decimal(cleaned.get('valor_beneficio') or 0)

        # recalcular sempre o valor_total para manter consistência
        try:
            cleaned['valor_total'] = (diaria * numero) + beneficio
        except Exception:
            pass

        return cleaned
