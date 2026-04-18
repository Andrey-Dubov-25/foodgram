import string
import random

from django.contrib.auth import get_user_model
from django.db import models

from api.validators import validate_positive_number
from core import constants


User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=constants.NAME_TAG_LEN,
        verbose_name='Название',
        help_text='Время для приема пищи: завтрак, обед, ужин'
    )
    slug = models.SlugField(
        max_length=constants.SLUG_TAG_LEN,
        unique=True,
        verbose_name='Слаг',
        help_text='Отображение в ссылке на сайте'
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает строковое представление."""
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=constants.NAME_INGREDIENT_LEN,
        verbose_name='Название',
        help_text='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=constants.MEASUREMENT_UNIT_INGREDIENT_LEN,
        verbose_name='Единицы',
        help_text='Единицы измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Возвращает строковое представление."""
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=constants.NAME_RECIPE_LEN,
        verbose_name='Название',
        help_text='Название рецепта'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание рецепта'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        help_text='Изображение готового блюда'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[validate_positive_number],
        verbose_name='Время приготовления',
        help_text='Время приготовления рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег(и)',
        help_text='Время для приема пищи: завтрак, обед, ужин'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиент(ы)',
        help_text='Название ингредиента(ов)'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Дата публикации рецепта'
    )
    short_link = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка',
        help_text='Короткая ссылка на рецепт'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает строковое представление."""
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        """Генерирует уникальный короткий код."""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(5))
            if not Recipe.objects.filter(short_link=code).exists():
                return code

class IngredientRecipe(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        help_text='Ингредиенты для рецепта',
        related_name='ingredient_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        help_text='Ингредиенты для рецепта',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[validate_positive_number],
        verbose_name='Количество',
        help_text='Количество ингредиента'
    )

    class Meta:
        verbose_name = 'ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецептов'

    def __str__(self):
        """Возвращает строковое представление."""
        return f'{self.ingredient} для {self.recipe}'


class Subscribe(models.Model):
    """Модель подписок на пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь',
        help_text='Пользователь, который подписывается'
    )
    subscribing = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_by',
        verbose_name='Подписка',
        help_text='Пользователь, на которого оформлена подписка'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'subscribing'),
                name='unique_subscribe'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление."""
        return f'{self.user} подписался на {self.subscribing}'


class Favorite(models.Model):
    """Модель списка избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
        help_text='Пользователь, который добавил рецепт в избранное'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites_by',
        verbose_name='Рецепт',
        help_text='Рецепт в избранном для пользователя'
    )

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление."""
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCard(models.Model):
    """Модель списка покупок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cards',
        verbose_name='Пользователь',
        help_text='Пользователь, который добавил рецепт в список покупок'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_card',
        verbose_name='Рецепт',
        help_text='Рецепт, который пользователь добавил в список покупок'
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_card'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление."""
        return f'{self.user} добавил в список покупок {self.recipe}'
