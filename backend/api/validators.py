import re

from rest_framework import serializers

from recipe.models import Recipe


class UsernameValidatorMixin:
    """Миксин валидации поля username."""

    def validate_username(self, value):
        """Валидация поля username на допустимые символы."""

        if not re.match(r'^[\w.@+-]+\Z$', value):
            raise serializers.ValidationError(
                'Недопустимый username. Доступно только буквы, цифры и '
                'символы @/./+/-/_.'
            )

        return value


class RecipeRepresentationMixin:
    """Миксин определения представления рецепта."""

    def to_representation(self, instance):
        """Возвращает расширенное представление для рецептов."""
        recipe = {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': (
                instance.recipe.image.url if instance.recipe.image else None
            ),
            'cooking_time': instance.recipe.cooking_time
        }
        return recipe


class RecipeDeleteFromMixin:
    """Миксин для удаления рецептов из списка."""

    def validate_recipe_id(self, value):
        """Проверка на существования рецепта. Если не найден - ошибка 404."""

        try:
            recipe = Recipe.objects.get(pk=value)
            self.context['recipe'] = recipe
            return value

        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'Рецепт не существует!'},
                code='not_found'
            )

    def validate(self, data):
        """
        Проверка на существование рецепта в корзине — если не найден - ошибка
        400.
        """
        user = self.context['request'].user
        recipe = self.context['recipe']

        if not self.relation_model.objects.filter(
            user=user, recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {'error': self.get_error_message()},
                code='bad_request'
            )

        return data
    
    def get_error_message(self):
        return 'Ошибка поиска.'
