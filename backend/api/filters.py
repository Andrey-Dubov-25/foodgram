import django_filters as filters

from recipe.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтрация по нескольким тегам."""
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author')

    class Meta:
        model = Recipe
        fields = ('tags',)

    def filter_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')

        if not value:
            return queryset

        return queryset.filter(tags__slug__in=tags)
