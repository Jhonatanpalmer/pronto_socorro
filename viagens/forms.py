from django import forms
from .models import Viagem
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

        # Ajustando exibição de hora de saída
        self.fields['hora_saida'].widget = forms.Select(choices=Viagem.horario_saida)
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
