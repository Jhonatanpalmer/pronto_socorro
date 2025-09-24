from django import forms
from django.contrib.auth.models import User, Group
from .models import GroupAccess
from regulacao.models import UBS, UsuarioUBS


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label='Grupos'
    )
    ubs = forms.ModelChoiceField(queryset=UBS.objects.filter(ativa=True).order_by('nome'), required=False, label='UBS do Usuário')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'password', 'groups']

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data['password']
        user.set_password(pwd)
        if commit:
            user.save()
            self.save_m2m()
            # Vincular UBS se fornecida
            ubs = self.cleaned_data.get('ubs')
            if ubs:
                UsuarioUBS.objects.update_or_create(user=user, defaults={'ubs': ubs})
            else:
                # Se não fornecida, garantir que não reste vínculo antigo (defensivo)
                UsuarioUBS.objects.filter(user=user).delete()
        return user


class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(label='Senha (deixe em branco para manter)', widget=forms.PasswordInput, required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple, label='Grupos'
    )
    ubs = forms.ModelChoiceField(queryset=UBS.objects.filter(ativa=True).order_by('nome'), required=False, label='UBS do Usuário')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser', 'password', 'groups']

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
            self.save_m2m()
            # Atualizar vínculo com UBS
            ubs = self.cleaned_data.get('ubs')
            if ubs:
                UsuarioUBS.objects.update_or_create(user=user, defaults={'ubs': ubs})
            else:
                UsuarioUBS.objects.filter(user=user).delete()
        return user


class GroupForm(forms.ModelForm):
    # Access flags
    can_pacientes = forms.BooleanField(label='Pacientes', required=False)
    can_viagens = forms.BooleanField(label='Viagens', required=False)
    can_tfd = forms.BooleanField(label='TFD', required=False)
    can_regulacao = forms.BooleanField(label='Regulação', required=False)
    can_users_admin = forms.BooleanField(label='Administração de Usuários/Grupos', required=False)

    class Meta:
        model = Group
        fields = ['name', 'can_pacientes', 'can_viagens', 'can_tfd', 'can_regulacao', 'can_users_admin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance: Group = kwargs.get('instance')
        if instance and instance.pk:
            access, _ = GroupAccess.objects.get_or_create(group=instance)
            self.fields['can_pacientes'].initial = access.can_pacientes
            self.fields['can_viagens'].initial = access.can_viagens
            self.fields['can_tfd'].initial = access.can_tfd
            self.fields['can_regulacao'].initial = access.can_regulacao
            self.fields['can_users_admin'].initial = access.can_users_admin

    def save(self, commit=True):
        group: Group = super().save(commit=commit)
        access, _ = GroupAccess.objects.get_or_create(group=group)
        access.can_pacientes = self.cleaned_data.get('can_pacientes', False)
        access.can_viagens = self.cleaned_data.get('can_viagens', False)
        access.can_tfd = self.cleaned_data.get('can_tfd', False)
        access.can_regulacao = self.cleaned_data.get('can_regulacao', False)
        access.can_users_admin = self.cleaned_data.get('can_users_admin', False)
        access.save()
        return group
