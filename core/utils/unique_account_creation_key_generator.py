"""
generate a unique order id
"""
from random import randint

from core.utils.random_string_generator import generate_string


def key_generator(instance):
    """
    This is for a Django project and it assumes your instance
    has a model with a key field.
    """
    size = randint(50, 64)
    key = generate_string(size=size)

    instance_class = instance.__class__
    qs_exists = instance_class.objects.filter(key=key).exists()
    if qs_exists:
        return key_generator(instance)
    return key
