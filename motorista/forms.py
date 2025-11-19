from django import forms
from .models import Motorista, ViagemMotorista
from viagens.models import DestinoViagem


class MotoristaForm(forms.ModelForm):
    def clean_nome_completo(self):
        nome = (self.cleaned_data.get('nome_completo') or '').strip()
        if not nome:
            raise forms.ValidationError('Informe o nome completo.')
        return nome.upper()

    def clean_cpf(self):
        import re
        cpf = (self.cleaned_data.get('cpf') or '').strip()
        # CPF opcional
        if not cpf:
            return None
        # Remove máscara e caracteres não numéricos
        digits = re.sub(r'\D+', '', cpf)
        # Aceita qualquer coisa com até 11 dígitos; deixa consistência de negócio para depois, se necessário
        if len(digits) > 11:
            digits = digits[-11:]
        return digits

    def clean_rg(self):
        import re
        rg = (self.cleaned_data.get('rg') or '').strip()
        return re.sub(r'\D+', '', rg)
    class Meta:
        model = Motorista
        fields = [
            'nome_completo', 'cpf', 'rg', 'data_nascimento',
            'cnh_numero', 'cnh_categoria', 'cnh_validade',
            'endereco', 'telefone', 'email',
            'matricula', 'data_admissao', 'situacao', 'escala_trabalho'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'cnh_validade': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
        }


class ViagemMotoristaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Pré-normaliza campos monetários/decimais se vierem com vírgula (pt-BR)
        data_source = None
        if len(args) > 0 and args[0] is not None:
            try:
                data_source = args[0]
            except Exception:
                data_source = None
        elif 'data' in kwargs and kwargs['data'] is not None:
            data_source = kwargs['data']
        if data_source is not None:
            data = data_source.copy()

            def norm_decimal(val: str) -> str:
                if val is None:
                    return val
                s = str(val).strip()
                if not s:
                    return s
                s = s.replace(' ', '')
                if ',' in s:
                    # Formato brasileiro: remover milhares e trocar vírgula por ponto
                    s = s.replace('.', '').replace(',', '.')
                # Remover quaisquer caracteres que não sejam dígitos, ponto ou sinal
                import re
                return re.sub(r'[^0-9.+-]', '', s)

            if 'valor_unitario_diaria' in data:
                data['valor_unitario_diaria'] = norm_decimal(data.get('valor_unitario_diaria'))
            if 'quantidade_horas_extras' in data:
                data['quantidade_horas_extras'] = norm_decimal(data.get('quantidade_horas_extras'))
            if 'valor_hora_extra' in data:
                data['valor_hora_extra'] = norm_decimal(data.get('valor_hora_extra'))
            # Reatribuir para kwargs para que o ModelForm use o data já normalizado
            kwargs['data'] = data
            # Se o dado veio em args[0], descartamos aquele e usamos kwargs['data']
            args = tuple()
        super().__init__(*args, **kwargs)
        # Definir mínimo como hoje para impedir datas anteriores no front
        from django.utils import timezone
        today = timezone.localdate().isoformat()
        for name in ('data_inicio', 'data_fim'):
            if name in self.fields:
                self.fields[name].widget.attrs['min'] = today
        destinos_qs = DestinoViagem.objects.filter(ativo=True).order_by('nome_cidade', 'uf')
        destino_choices = [('', 'Selecione...')] + [
            (f"{d.nome_cidade}/{d.uf}", f"{d.nome_cidade}/{d.uf}") for d in destinos_qs
        ]
        if 'destino' in self.fields:
            self.fields['destino'].widget = forms.Select(choices=destino_choices)
            self.fields['destino'].label = 'Destino'

        # Ocultar campos de horas extras na interface, mantendo valores zerados
        for nome in ('quantidade_horas_extras', 'valor_hora_extra'):
            if nome in self.fields:
                self.fields[nome].initial = self.instance.__dict__.get(nome, 0) or 0
                self.fields[nome].widget = forms.HiddenInput()
        if 'justificativa_horas_extras' in self.fields:
            self.fields['justificativa_horas_extras'].initial = ''
            self.fields['justificativa_horas_extras'].widget = forms.HiddenInput()

    class Meta:
        model = ViagemMotorista
        fields = [
            'motorista', 'data_inicio', 'data_fim', 'origem', 'destino', 'veiculo',
            'dias_viagem', 'quantidade_diarias', 'valor_unitario_diaria',
            'quantidade_horas_extras', 'valor_hora_extra', 'justificativa_horas_extras',
            'motivo_viagem', 'observacoes'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'valor_unitario_diaria': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Ex.: 150,00',
                'autocomplete': 'off',
            }),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        di = cleaned.get('data_inicio')
        df = cleaned.get('data_fim')
        from django.utils import timezone
        today = timezone.localdate()
        # Não permitir datas anteriores a hoje
        if di and di < today:
            self.add_error('data_inicio', 'A data de início não pode ser anterior à data de hoje.')
        if df and df < today:
            self.add_error('data_fim', 'A data de fim não pode ser anterior à data de hoje.')
        if di and df and df < di:
            self.add_error('data_fim', 'A data de fim não pode ser anterior à data de início.')
        # Campos obrigatórios principais
        obrig_principais = {
            'motorista': cleaned.get('motorista'),
            'data_inicio': di,
            'data_fim': df,
            'veiculo': cleaned.get('veiculo'),
            'valor_unitario_diaria': cleaned.get('valor_unitario_diaria'),
            'motivo_viagem': (cleaned.get('motivo_viagem') or '').strip(),
        }
        for campo, val in obrig_principais.items():
            if not val:
                self.add_error(campo, 'Campo obrigatório.')

        # Valores monetários entram como string se mascarados no front; Django DecimalField já converte.
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.quantidade_horas_extras = 0
        obj.valor_hora_extra = 0
        obj.justificativa_horas_extras = ''
        if commit:
            obj.save()
        return obj
