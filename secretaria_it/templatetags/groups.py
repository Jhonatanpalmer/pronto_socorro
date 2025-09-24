from django import template

register = template.Library()

@register.filter(name='sec_in_group')
def sec_in_group(user, group_name: str) -> bool:
    """Namespaced variant to avoid clashing with project-level 'groups' lib."""
    try:
        return bool(user and user.is_authenticated and user.groups.filter(name=group_name).exists())
    except Exception:
        return False
