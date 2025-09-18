from django.contrib import admin
from django.urls import path, include
from secretaria_it.views import dashboard_view, logout_ajax_view
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Raiz do site: redireciona para login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # Dashboard protegido
    path('dashboard/', dashboard_view, name='dashboard'),

    # Apps
    path('viagens/', include('viagens.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('tfd/', include('tfd.urls')),

    # Auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='secretaria_it/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/logout-ajax/', logout_ajax_view, name='logout-ajax'),
]
