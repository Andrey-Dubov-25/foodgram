import string
from random import choice
from django.contrib.auth import get_user_model


User = get_user_model()


def get_short_url(length=5):
    result = ''
    letters = string.ascii_letters
    digits = string.digits

    for _ in range(length):
        result += choice(letters)
        result += choice(digits)
    
    return result
