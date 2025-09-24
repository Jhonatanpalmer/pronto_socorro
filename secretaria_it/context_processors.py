from typing import Dict
from .access import user_has_access, is_ubs_user


def group_flags(request) -> Dict[str, bool]:
    """Adds simple group booleans to the template context.
    - is_regulacao: user in 'Regulação'
    - is_ubs: user in 'UBS'
    """
    user = getattr(request, 'user', None)

    def in_group(name: str) -> bool:
        try:
            return bool(user and user.is_authenticated and user.groups.filter(name=name).exists())
        except Exception:
            return False

    return {
        'is_regulacao': in_group('Regulação'),
        'is_ubs': in_group('UBS'),
        # Access flags (by GroupAccess)
        'acc_pacientes': user_has_access(user, 'pacientes'),
        'acc_viagens': user_has_access(user, 'viagens'),
        'acc_tfd': user_has_access(user, 'tfd'),
        'acc_regulacao': user_has_access(user, 'regulacao'),
        'acc_users_admin': user_has_access(user, 'users_admin'),
        # UBS persona
        'is_ubs_user': is_ubs_user(user),
        'ubs_atual': getattr(getattr(user, 'perfil_ubs', None), 'ubs', None),
    }
