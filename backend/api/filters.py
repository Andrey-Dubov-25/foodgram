import django_filters as filters
from recipe.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author_id')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')

        if not value:
            return queryset

        return queryset.filter(tags__slug__in=tags)
