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
    model = IngredientRecipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class ReceipAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInLine,)
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('tags',)
    list_display_links = ('name',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribing')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCard)
class ShoppingCard(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(IngredientRecipe)
admin.site.register(Tag)
