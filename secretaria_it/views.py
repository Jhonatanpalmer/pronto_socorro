from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.conf import settings
from .forms import UserCreateForm, UserUpdateForm, GroupForm
from .access import user_has_access

@login_required
def dashboard_view(request):
    """
    Dashboard principal mostrando os aplicativos disponíveis para o usuário.
    """
    apps = []

    # App Pacientes
    if 'pacientes' in settings.INSTALLED_APPS and user_has_access(request.user, 'pacientes'):
        apps.append({
            'nome': 'Gestão de Pacientes',
            'descricao': 'Cadastre, edite e visualize os pacientes.',
            'url': 'paciente_list',
            'icone': 'bi-people-fill',
            'cor': 'primary'
        })
    

    # App Viagens
    if 'viagens' in settings.INSTALLED_APPS and user_has_access(request.user, 'viagens'):
        apps.append({
            'nome': 'Gestão de Viagens',
            'descricao': 'Acompanhe viagens, horários e status.',
            'url': 'viagem-list',
            'icone': 'bi-truck',
            'cor': 'success'
        })
    

    # App TFD
    if 'tfd' in settings.INSTALLED_APPS and user_has_access(request.user, 'tfd'):
        apps.append({
            'nome': 'Gestão de TFD',
            'descricao': 'Gerencie os tratamentos fora do domicílio.',
            'url': 'tfd-list',
            'icone': 'bi-hospital-fill',
            'cor': 'info'
        })
    

    # App Regulação
    if 'regulacao' in settings.INSTALLED_APPS and user_has_access(request.user, 'regulacao'):
        apps.append({
            'nome': 'Regulação',
            'descricao': 'Gerencie solicitações de exames e consultas',
            'url': 'regulacao-dashboard',
            'icone': 'bi-clipboard-check-fill',
            'cor': 'warning'
        })
    
    # App Veículos - Abastecimentos
    if 'veiculos' in settings.INSTALLED_APPS and user_has_access(request.user, 'veiculos'):
        apps.append({
            'nome': 'Veículos - Abastecimentos',
            'descricao': 'Registre e acompanhe abastecimentos dos veículos.',
            'url': 'abastecimento-list',
            'icone': 'bi-fuel-pump',
            'cor': 'primary'
        })
    
    # App RH
    if 'rh' in settings.INSTALLED_APPS and user_has_access(request.user, 'rh'):
        apps.append({
            'nome': 'RH',
            'descricao': 'Cadastro e gestão de funcionários (RH).',
            'url': 'rh-funcionario-list',
            'icone': 'bi-people-fill',
            'cor': 'success'
        })
    
    # App Motorista
    if 'motorista' in settings.INSTALLED_APPS and user_has_access(request.user, 'motorista'):
        apps.append({
            'nome': 'Motoristas',
            'descricao': 'Cadastro de motoristas e controle de viagens.',
            'url': 'motorista-home',
            'icone': 'bi-person-vcard',
            'cor': 'info'
        })


    # Aqui você pode adicionar outros apps existentes, apenas se tiver URLs válidas

    return render(request, 'secretaria_it/dashboard.html', {'apps': apps})


# ====== Gestão de Usuários e Grupos ======

def _staff_or_super(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))

def _users_admin_allowed(user):
    # Superusers always allowed; otherwise require users_admin access flag
    return bool(user and user.is_authenticated and (user.is_superuser or user_has_access(user, 'users_admin')))


@login_required
@user_passes_test(_users_admin_allowed)
def users_list(request):
    qs = User.objects.all().order_by('username')
    return render(request, 'secretaria_it/users/list.html', {'users': qs})


@login_required
@user_passes_test(_users_admin_allowed)
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users-list')
    else:
        form = UserCreateForm()
    return render(request, 'secretaria_it/users/form.html', {'form': form, 'title': 'Novo Usuário'})


@login_required
@user_passes_test(_users_admin_allowed)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users-list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'secretaria_it/users/form.html', {'form': form, 'title': f'Editar Usuário: {user.username}'})


@login_required
@user_passes_test(_users_admin_allowed)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('users-list')
    return render(request, 'secretaria_it/users/confirm_delete.html', {'obj': user, 'title': f'Excluir {user.username}'})


@login_required
@user_passes_test(_users_admin_allowed)
def groups_list(request):
    qs = Group.objects.all().order_by('name')
    return render(request, 'secretaria_it/users/groups_list.html', {'groups': qs})


@login_required
@user_passes_test(_users_admin_allowed)
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('groups-list')
    else:
        form = GroupForm()
    return render(request, 'secretaria_it/users/group_form.html', {'form': form, 'title': 'Novo Grupo'})


@login_required
@user_passes_test(_users_admin_allowed)
def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('groups-list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'secretaria_it/users/group_form.html', {'form': form, 'title': f'Editar Grupo: {group.name}'})


@login_required
@user_passes_test(_users_admin_allowed)
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        return redirect('groups-list')
    return render(request, 'secretaria_it/users/confirm_delete.html', {'obj': group, 'title': f'Excluir {group.name}'})

