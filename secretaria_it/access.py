from typing import Optional
from django.contrib.auth.models import Group, User
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.functional import cached_property

ACCESS_KEYS = {
    'pacientes': 'can_pacientes',
    'viagens': 'can_viagens',
    'tfd': 'can_tfd',
    'regulacao': 'can_regulacao',
    'users_admin': 'can_users_admin',
}


def group_has_access(group: Group, key: str) -> bool:
    flag = ACCESS_KEYS.get(key)
    if not flag:
        return False
    try:
        access = getattr(group, 'access', None)
        if not access:
            return False
        return bool(getattr(access, flag))
    except Exception:
        return False


def user_has_access(user: User, key: str) -> bool:
    if not (user and user.is_authenticated):
        return False
    # Superusers always have access
    if user.is_superuser:
        return True
    flag = ACCESS_KEYS.get(key)
    if not flag:
        return False
    try:
        groups = user.groups.all()
        for g in groups:
            if group_has_access(g, key):
                return True
        return False
    except Exception:
        return False


def is_ubs_user(user: User) -> bool:
    """Return True if user is linked to a specific UBS via regulacao.UsuarioUBS."""
    if not (user and user.is_authenticated):
        return False
    try:
        return bool(getattr(user, 'perfil_ubs', None))
    except Exception:
        return False


def require_access(key: str):
    """Decorator for FBVs to enforce access to a module by key.
    Example: @login_required @require_access('pacientes')
    """
    def _decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if user_has_access(request.user, key):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Acesso negado para este módulo.')
        return _wrapped
    return _decorator


class AccessRequiredMixin:
    """CBV mixin that denies access if user lacks given access_key.
    Usage: class MyView(AccessRequiredMixin, LoginRequiredMixin, ListView):
        access_key = 'pacientes'
    """
    access_key: Optional[str] = None

    @cached_property
    def _has_access(self) -> bool:
        return bool(self.access_key and user_has_access(self.request.user, self.access_key))

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        if not request.user.is_authenticated:
            return redirect('login')
        if not self.access_key or not self._has_access:
            return HttpResponseForbidden('Acesso negado para este módulo.')
        return super().dispatch(request, *args, **kwargs)
