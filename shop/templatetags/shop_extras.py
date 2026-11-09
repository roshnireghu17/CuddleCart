from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter
def star_range(value):
    """Returns range(1,6) so templates can loop to draw 5 stars."""
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        value = 0
    return range(1, 6), value


@register.simple_tag
def stars_filled(value):
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0
