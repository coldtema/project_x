from django import template
import math

register = template.Library()

@register.filter
def minus(value, arg):
    return int(value) - int(arg)


@register.filter
def abs_tag(value):
    return abs(value)