from django import forms
from django.core.validators import MaxLengthValidator
from .models import FuncionarioRH, AtestadoMedico
import re


class FuncionarioRHForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        # Permitir máscaras (com pontos e hífen) sem estourar o limite do campo
        for field_name, size in (('cpf', 14), ('cep', 9)):
            field = self.fields[field_name]
            field.max_length = size
            field.widget.attrs['maxlength'] = size
            # Substitui validador de tamanho padrão (11/8) por novo limite mais amplo
            field.validators = [
                validator for validator in field.validators
                if not isinstance(validator, MaxLengthValidator)
            ]
            field.validators.append(MaxLengthValidator(size))
    def clean_cpf(self):
        cpf = (self.cleaned_data.get('cpf') or '').strip()
        # Keep only digits
        cpf_digits = re.sub(r'\D+', '', cpf)
        if len(cpf_digits) != 11 or cpf_digits == cpf_digits[0] * 11:
            raise forms.ValidationError('CPF inválido.')
        # Validate CPF check digits
        def calc_digit(nums, factor):
            total = 0
            for n in nums:
                total += int(n) * factor
                factor -= 1
            mod = total % 11
            return '0' if mod < 2 else str(11 - mod)
        d1 = calc_digit(cpf_digits[:9], 10)
        d2 = calc_digit(cpf_digits[:10], 11)
        if cpf_digits[-2:] != d1 + d2:
            raise forms.ValidationError('CPF inválido.')
        return cpf_digits

    def clean_telefone(self):
        tel = (self.cleaned_data.get('telefone') or '').strip()
        tel_digits = re.sub(r'\D+', '', tel)
        if tel_digits and (len(tel_digits) < 10 or len(tel_digits) > 11):
            raise forms.ValidationError('Telefone deve ter 10 ou 11 dígitos (DDD + número).')
        return tel_digits
    class Meta:
        model = FuncionarioRH
        fields = [
            'nome', 'cpf', 'rg', 'data_nascimento', 'telefone', 'email',
            'cargo', 'situacao', 'vinculo', 'data_admissao', 'data_desligamento',
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'uf', 'setor_lotacao',
            'observacoes', 'doc_rg', 'doc_ctps', 'doc_comprovante_endereco'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'data_desligamento': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_rg(self):
        rg = (self.cleaned_data.get('rg') or '').strip()
        return re.sub(r'\D+', '', rg)

    def clean_cep(self):
        cep = (self.cleaned_data.get('cep') or '').strip()
        cep_digits = re.sub(r'\D+', '', cep)
        if cep_digits and len(cep_digits) != 8:
            raise forms.ValidationError('CEP deve ter 8 dígitos.')
        return cep_digits

    def clean(self):
        cleaned = super().clean()
        # Validate uploaded file sizes (max 10MB each)
        for field_name in ['doc_rg', 'doc_ctps', 'doc_comprovante_endereco']:
            f = cleaned.get(field_name)
            # When not changed, value may be None or a FieldFile; check for uploaded file-like with size attr
            if hasattr(f, 'size') and f.size and f.size > self.MAX_UPLOAD_SIZE:
                self.add_error(field_name, 'Arquivo muito grande. Tamanho máximo permitido: 10MB.')
        return cleaned


class AtestadoMedicoForm(forms.ModelForm):
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dias'].widget.attrs.update({'readonly': 'readonly', 'min': 1})

    class Meta:
        model = AtestadoMedico
        fields = [
            'funcionario', 'data_inicio', 'data_fim', 'dias', 'cid', 'medico', 'crm', 'motivo', 'arquivo'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        di = cleaned.get('data_inicio')
        df = cleaned.get('data_fim')
        if di and df:
            if df < di:
                self.add_error('data_fim', 'Data final não pode ser anterior à data inicial.')
            else:
                cleaned['dias'] = (df - di).days + 1
        dias = cleaned.get('dias') or 0
        if dias <= 0 and 'data_inicio' not in self.errors and 'data_fim' not in self.errors:
            self.add_error('dias', 'Dias deve ser maior que zero.')
        f = cleaned.get('arquivo')
        if hasattr(f, 'size') and f.size and f.size > self.MAX_UPLOAD_SIZE:
            self.add_error('arquivo', 'Arquivo muito grande. Máximo 10MB.')
        return cleaned
