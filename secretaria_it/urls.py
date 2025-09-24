from django.contrib import admin
from django.urls import path, include
from secretaria_it.views import (
    dashboard_view,
    users_list, user_create, user_update, user_delete,
    groups_list, group_create, group_update, group_delete,
)
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    # Raiz do site: redireciona para login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # Dashboard protegido
    path('dashboard/', dashboard_view, name='dashboard'),

    # Apps
    path('viagens/', include('viagens.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('tfd/', include('tfd.urls')),
    path('regulacao/', include('regulacao.urls')),

    # Auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='secretaria_it/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Users/Groups management
    path('admin/usuarios/', users_list, name='users-list'),
    path('admin/usuarios/novo/', user_create, name='user-create'),
    path('admin/usuarios/<int:pk>/editar/', user_update, name='user-update'),
    path('admin/usuarios/<int:pk>/excluir/', user_delete, name='user-delete'),
    path('admin/grupos/', groups_list, name='groups-list'),
    path('admin/grupos/novo/', group_create, name='group-create'),
    path('admin/grupos/<int:pk>/editar/', group_update, name='group-update'),
    path('admin/grupos/<int:pk>/excluir/', group_delete, name='group-delete'),

    # Django Admin (keep last so it doesn't swallow custom /admin/... routes)
    path('admin/', admin.site.urls),
]
