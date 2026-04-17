import django_filters as filters

from core import utils
from recipe.models import Recipe, Tag, ShoppingCard, Favorite


class RecipeFilter(filters.FilterSet):
    """Фильтрация по нескольким тегам."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags',
        to_field_name='slug',
        method='filter_tags',
        queryset=Tag.objects.all()

    )
    is_in_shopping_cart = filters.CharFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.CharFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def filter_tags(self, queryset, name, value):
        """Возвращает QuerySet с наличием хотя бы одного из тегов в рецепте."""
        if not value:
            return queryset

        return queryset.filter(tags__in=value).distinct()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Возвращает QuerySet с рецептами в списке покупок."""
        return self.filter_by_param(
            filter_self=self,
            filter_queryset=queryset,
            filter_value=value,
            filter_model=ShoppingCard
        )

    def filter_is_favorited(self, queryset, name, value):
        """Возвращает QuerySet с рецептами в избранном."""
        return self.filter_by_param(
            filter_self=self,
            filter_queryset=queryset,
            filter_value=value,
            filter_model=Favorite
        )

    @staticmethod
    def filter_by_param(
        filter_self, filter_queryset, filter_value, filter_model
    ):
        """Возвращает QuerySet с отфильтрованными по параметру рецептами."""
        user = utils.get_self_user(filter_self)

        if not bool(filter_value):
            return filter_queryset

        if not user.is_authenticated:
            return filter_queryset

        param = filter_model.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)

        return filter_queryset.filter(id__in=param)
