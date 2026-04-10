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

def get_user(request):
    """Возвращает текущего пользователя через request."""
    return request.user

def get_self_user(self):
    """Возвращает текущего пользователя через self."""
    return self.request.user

def get_method():
    """Возвращает параметр запроса get."""
    return ['get']

def post_method():
    """Возвращает параметр запроса post."""
    return ['post']

def put_delete_methods():
    """Возвращает параметры запроса pud и delete."""
    return ['put', 'delete']

def post_delete_methods():
    """Возвращает параметры запроса post и delete."""
    return ['post', 'delete']

def get_request(request):
    """Возвращает словарь контекста с объектом запроса."""
    return {'request': request}

def get_recipe_id(pk):
    """Возвращает первичный ключ рецепта."""
    return {'recipe_id': pk}
