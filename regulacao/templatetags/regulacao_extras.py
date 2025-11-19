from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Acessa um valor em dicionário usando chave dinâmica no template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter  
def get_attr(obj, attr_name):
    """Obtém atributo de um objeto usando nome dinâmico."""
    try:
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        return None

@register.filter
def make_key(paciente_id, data):
    """Cria uma chave combinando paciente_id e data para busca no dicionário."""
    return f"{paciente_id}_{data}"