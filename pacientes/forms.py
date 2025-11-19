from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nome', 'cpf', 'cns', 'data_nascimento',
            'nome_mae', 'nome_pai', 'telefone',
            'logradouro', 'numero', 'bairro', 'cep',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'cns': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CNS'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nome_mae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo da mãe'}),
            'nome_pai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do pai'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua/Avenida/Travessa'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
        }

    def clean_cpf(self):
        """Remove formatação do CPF (pontos e hífen) antes de salvar"""
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove todos os caracteres não numéricos
            cpf = ''.join(filter(str.isdigit, cpf))
        return cpf
