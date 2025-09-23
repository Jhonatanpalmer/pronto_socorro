from django import forms
from .models import Viagem
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
        try:
            posted = self.data.get(self.add_prefix('paciente')) if hasattr(self, 'data') else None
            if posted:
                ids.add(int(posted))
        except (ValueError, TypeError):
            pass
        if getattr(self.instance, 'paciente_id', None):
            ids.add(int(self.instance.paciente_id))
        self.fields['paciente'].queryset = Paciente.objects.filter(pk__in=ids) if ids else Paciente.objects.none()

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

