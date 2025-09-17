from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
