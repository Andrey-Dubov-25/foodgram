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

        if not tags:
            return queryset
        
        for tag in tags:
            queryset = queryset.filter(tags__slug=tag)

        return queryset.distinct()
