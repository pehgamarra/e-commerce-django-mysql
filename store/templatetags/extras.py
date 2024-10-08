from django import template

register = template.Library()

@register.filter(name='range')
def num_range(value):
    return range(1, value + 1)

@register.filter
def range_filter(value):
    return range(1, value + 1)