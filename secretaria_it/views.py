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

    # App TFD
    try:
        from tfd.urls import urlpatterns as tfd_urls
        apps.append({
            'nome': 'Gestão de TFD',
            'descricao': 'Gerencie os tratamentos fora do domicílio.',
            'url': 'tfd-list',
            'icone': 'bi-hospital-fill',
            'cor': 'info'
        })
    except ImportError:
        pass  # TFD não disponível

    # App Regulação
    try:
        from regulacao.urls import urlpatterns as regulacao_urls
        apps.append({
            'nome': 'Regulação de Exames',
            'descricao': 'Gerencie solicitações e autorizações de exames.',
            'url': 'regulacao-dashboard',
            'icone': 'bi-clipboard-check-fill',
            'cor': 'warning'
        })
    except ImportError:
        pass  # Regulação não disponível

    # Aqui você pode adicionar outros apps existentes, apenas se tiver URLs válidas

    return render(request, 'secretaria_it/dashboard.html', {'apps': apps})
