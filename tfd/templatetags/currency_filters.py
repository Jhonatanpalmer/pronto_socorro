from django import template

register = template.Library()


@register.filter
def br_currency(value):
    """Format a number as Brazilian currency 'R$ 1.234,56'.

    Accepts Decimal or float or int. Returns a safe string.
    """
    try:
        # Try to convert to float first (Decimal will work too)
        v = float(value)
    except Exception:
        return value

    # format with two decimals and thousands separator
    # use Python formatting then replace separators to Brazilian style
    s = f"{v:,.2f}"
    # Python uses ',' for thousands and '.' for decimal in en_US; swap
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"R$ {s}"
