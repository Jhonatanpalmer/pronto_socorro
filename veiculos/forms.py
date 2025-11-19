from django import forms
from datetime import datetime, time
from django.utils import timezone
from veiculos.models import (
    Abastecimento,
    Veiculo,
    LocalManutencao,
    ManutencaoVeiculo,
)
from motorista.models import Motorista


class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = [
            'placa', 'modelo', 'tipo', 'capacidade', 'combustivel', 'motorista'
        ]

class AbastecimentoForm(forms.ModelForm):
    # Mostrar apenas a data; a hora será preenchida automaticamente no backend
    data_hora = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Carregar todos os motoristas cadastrados (módulo Motorista)
        if 'motorista' in self.fields:
            self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome_completo')
        # Definir data mínima como hoje (não permite dias anteriores)
        if 'data_hora' in self.fields:
            today = timezone.localdate().isoformat()
            self.fields['data_hora'].widget.attrs['min'] = today
    class Meta:
        model = Abastecimento
        fields = [
            "motorista",
            "veiculo",
            "tipo_veiculo",
            "tipo_combustivel",
            "local_abastecimento",
            "data_hora",
            "observacao",
        ]
        widgets = {}

    def clean_data_hora(self):
        """Recebe apenas a data do formulário, valida que não é passada e combina com a hora atual local."""
        d = self.cleaned_data.get('data_hora')
        if d is None:
            return d
        today = timezone.localdate()
        if d < today:
            raise forms.ValidationError('A data do abastecimento não pode ser anterior à data de hoje.')
        now = timezone.localtime()
        dt = datetime.combine(d, time(hour=now.hour, minute=now.minute, second=now.second))
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt


class LocalManutencaoForm(forms.ModelForm):
    class Meta:
        model = LocalManutencao
        fields = [
            "nome",
            "cidade",
            "responsavel",
            "telefone",
            "observacoes",
        ]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class ManutencaoVeiculoForm(forms.ModelForm):
    class Meta:
        model = ManutencaoVeiculo
        fields = [
            "veiculo",
            "tipo",
            "local",
            "data_envio",
            "data_retorno",
            "descricao_problema",
            "servicos_realizados",
            "status",
        ]
        widgets = {
            "data_envio": forms.DateInput(attrs={"type": "date"}),
            "data_retorno": forms.DateInput(attrs={"type": "date"}),
            "descricao_problema": forms.Textarea(attrs={"rows": 4}),
            "servicos_realizados": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        envio = cleaned.get("data_envio")
        retorno = cleaned.get("data_retorno")
        if envio and retorno and retorno < envio:
            self.add_error("data_retorno", "A data de devolução não pode ser anterior à data de envio.")
        return cleaned
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["data_envio"].disabled = True
            self.fields["data_envio"].required = False
