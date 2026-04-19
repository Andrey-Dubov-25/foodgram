from typing import Any, Union, Self

from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request

from users.models import CustomUser


StringList = list[str]
DictAny = dict[str, Any]


def get_user(request: Request) -> Union[CustomUser, AnonymousUser]:
    """Возвращает текущего пользователя через request."""
    return request.user


def get_self_user(self: Self) -> Union[CustomUser, AnonymousUser]:
    """Возвращает текущего пользователя через self."""
    return self.request.user


def get_method() -> StringList:
    """Возвращает параметр запроса get."""
    return ['get']


def post_method() -> StringList:
    """Возвращает параметр запроса post."""
    return ['post']


def put_delete_methods() -> StringList:
    """Возвращает параметры запроса pud и delete."""
    return ['put', 'delete']


def post_delete_methods() -> StringList:
    """Возвращает параметры запроса post и delete."""
    return ['post', 'delete']


def list_retrieve_methods() -> StringList:
    """Возвращает параметры запроса post и delete."""
    return ['list', 'retrieve']


def get_request(request: Request) -> dict[str, Request]:
    """Возвращает словарь контекста с объектом запроса."""
    return {'request': request}


def get_recipe_id(pk: int) -> dict[str, int]:
    """Возвращает первичный ключ рецепта."""
    return {'recipe_id': pk}


def get_email(data: DictAny) -> str:
    """Возвращает email пользователя."""
    return data['email']


def get_password(data: DictAny) -> str:
    """Возвращает password пользователя."""
    return data['password']


def get_username(data: DictAny) -> str:
    """Возвращает username пользователя."""
    return data['username']


def get_context_request(self: Self):
    """Возвращает объект request из контекста."""
    return self.context.get('request')
