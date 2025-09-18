from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def dashboard_view(request):
    """
    Dashboard principal mostrando os aplicativos disponíveis para o usuário.
    """
    apps = []

    # App Pacientes
    try:
        from pacientes.urls import urlpatterns as pacientes_urls
        apps.append({
            'nome': 'Gestão de Pacientes',
            'descricao': 'Cadastre, edite e visualize os pacientes.',
            'url': 'paciente_list',
            'icone': 'bi-people-fill',
            'cor': 'primary'
        })
    except ImportError:
        pass  # Pacientes não disponível

    # App Viagens
    try:
        from viagens.urls import urlpatterns as viagens_urls
        apps.append({
            'nome': 'Gestão de Viagens',
            'descricao': 'Acompanhe viagens, horários e status.',
            'url': 'viagem-list',
            'icone': 'bi-truck',
            'cor': 'success'
        })
    except ImportError:
        pass  # Viagens não disponível

    # Aqui você pode adicionar outros apps existentes, apenas se tiver URLs válidas

    return render(request, 'secretaria_it/dashboard.html', {'apps': apps})


@require_POST
def logout_ajax_view(request):
    """
    View para logout via AJAX.
    """
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logout realizado com sucesso'})
    return JsonResponse({'success': False, 'message': 'Usuário não autenticado'})
