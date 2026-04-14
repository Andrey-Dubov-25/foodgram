from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCard,
    Subscribe,
    Tag,
)


class IngredientRecipeInLine(admin.TabularInline):
    """Ингредиенты для представления в рецептах."""

    model = IngredientRecipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ингредиенты."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class ReceipAdmin(admin.ModelAdmin):
    """Рецепты."""

    inlines = (IngredientRecipeInLine,)
    list_display = (
        'name',
        'get_author',
        'text',
        'cooking_time',
        'get_tags',
        'get_ingredients',
        'pub_date',
        'favorites_count'
    )
    search_fields = ('name', 'author__username', 'author__first_name')
    list_filter = ('tags',)
    list_display_links = ('name',)

    def get_author(self, obj):
        """Возвращает автора рецепта."""
        return obj.author.username

    get_author.short_description = 'Автор'

    def get_queryset(self, request):
        """Возвращает Queryset рецептов со связями в избранном."""
        qs = super().get_queryset(request)
        return qs.prefetch_related('favorites_by', 'tags', 'ingredients')

    def favorites_count(self, obj):
        """Возвращает количество добавлений рецептов в избранное."""
        return obj.favorites_by.count()

    favorites_count.short_description = 'В избранном'

    def get_tags(self, obj):
        """Возвращает теги рецепта."""
        all_tags = [tag.name for tag in obj.tags.all()]
        return ', '.join(all_tags)

    get_tags.short_description = 'Теги'

    def get_ingredients(self, obj):
        """Возвращает ингредиенты рецепта."""
        all_ingredients = [
            ingredient.ingredient.name
            for ingredient in obj.recipe_ingredients.all()
        ]

        return ', '.join(all_ingredients)

    get_ingredients.short_description = 'Ингредиенты'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Подписки пользователей."""

    list_display = ('user', 'subscribing')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Рецепты в избранном."""

    list_display = ('user', 'recipe')


@admin.register(ShoppingCard)
class ShoppingCard(admin.ModelAdmin):
    """Корзина покупок пользователей."""

    list_display = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Ингредиенты."""

    list_display = ('name', 'slug')
    search_fields = ('name',)
