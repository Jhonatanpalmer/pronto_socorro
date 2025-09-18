from django import forms
from .models import Viagem
from .models import Paciente
from django.core.exceptions import ValidationError
import datetime

class ViagemForm(forms.ModelForm):
    class Meta:
        model = Viagem
        fields = '__all__'

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

        # Ajustando exibição de hora de saída (30 em 30 minutos)
        if hasattr(self.instance, 'hora_saida'):
            self.fields['hora_saida'].widget = forms.Select(choices=self.instance._meta.get_field('hora_saida').choices)
        else:
            self.fields['hora_saida'].widget = forms.Select(choices=[])

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


# pacientes/forms.py
from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'endereco': forms.Textarea(attrs={'rows': 2}),
        }

        error_messages = {
            'nome': {'required': 'Informe o nome do paciente.'},
            'cpf': {'invalid': 'CPF inválido.'},
        }
