from django import template

register = template.Library()

@register.filter
def in_list(value, the_list):
    return value in the_list

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def get_item(dictionary, key):
    # Guard: if not a dict, return 0 safely
    if not isinstance(dictionary, dict):
        return 0
    return dictionary.get(key, 0)