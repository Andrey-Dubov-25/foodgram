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


def list_retrieve_methods():
    """Возвращает параметры запроса post и delete."""
    return ['list', 'retrieve']


def get_request(request):
    """Возвращает словарь контекста с объектом запроса."""
    return {'request': request}


def get_recipe_id(pk):
    """Возвращает первичный ключ рецепта."""
    return {'recipe_id': pk}


def get_email(data):
    """Возвращает email пользователя."""
    return data['email']


def get_password(data):
    """Возвращает password пользователя."""
    return data['password']


def get_username(data):
    """Возвращает username пользователя."""
    return data['username']


def get_context_request(self):
    """Возвращает объект request из контекста."""
    return self.context.get('request')
