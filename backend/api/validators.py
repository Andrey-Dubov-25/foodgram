from django.core.exceptions import ValidationError


def validate_positive_number(value):
    """Валидация поля cooking_time."""
    if value < 1:
        raise ValidationError('Укажите положительное число.')
