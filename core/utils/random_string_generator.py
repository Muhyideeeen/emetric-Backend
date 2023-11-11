"""
Module to generate a random string
"""

import random
import string


def generate_string(size=10, chars=string.ascii_lowercase + string.digits):
    """
    generate a random string with a default size
    :param size: size of the string to generate
    :param chars: characters involved to generate string
    :return:
    """
    return "".join(random.choice(chars) for _ in range(size))
