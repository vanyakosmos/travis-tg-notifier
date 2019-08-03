from django import template

register = template.Library()


@register.filter
def duration(d: int):
    m = d // 60
    s = d % 60
    return f"{m}:{s:0d}"
