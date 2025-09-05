from django import forms
from .models import Viagem

class ViagemForm(forms.ModelForm):
    class Meta:
        model = Viagem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ViagemForm, self).__init__(*args, **kwargs)

        # Ajustando exibição de hora de saída
        self.fields['hora_saida'].widget = forms.Select(choices=Viagem.horario_saida)
