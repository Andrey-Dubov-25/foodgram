import django_filters as filters
from recipe.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.BaseInFilter(field_name='tags__slug', lookup_expr='in')
    author = filters.NumberFilter(field_name='author_id')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
