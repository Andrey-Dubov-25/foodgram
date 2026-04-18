from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientReadOnlyModelViewSet,
    RecipeList,
    TagReadOnlyModelViewSet,
    UserViewSet,
    ShortLinkRedirectView
)


router = DefaultRouter()
router.register('users', UserViewSet, basename='myuser')
router.register('recipes', RecipeList, basename='recipe')
router.register('tags', TagReadOnlyModelViewSet)
router.register('ingredients', IngredientReadOnlyModelViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/<int:pk>/get-link/',
        RecipeList.as_view({'get': 'get_link'}),
        name='recipe-short-link'
    ),

    # Маршрут для обработки коротких ссылок (/s/<hash>)
    re_path(
        r'^s/(?P<code>[a-zA-Z0-9]+)$',
        ShortLinkRedirectView.as_view(),
        name='short-link-redirect'
    ),
]
