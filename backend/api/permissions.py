from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):
    """Доступ к редактированию только автору или для чтения."""

    def has_permission(self, request, view):
        """Доступ к редактированию только авторизированным пользователям."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Разрешение на редактирование только автору или администратору."""
        return request.user == obj.author or request.user.is_staff
