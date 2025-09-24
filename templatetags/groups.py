from django import template

register = template.Library()

@register.filter(name='in_group')
def in_group(user, group_name: str) -> bool:
    try:
        return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())
    except Exception:
        return False
