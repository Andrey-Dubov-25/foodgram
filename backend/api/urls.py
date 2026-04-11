from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientReadOnlyModelViewSet,
    RecipeList,
    TagReadOnlyModelViewSet,
    UserViewSet,
)


router = DefaultRouter()
router.register('users', UserViewSet)
router.register('recipes', RecipeList)
router.register('tags', TagReadOnlyModelViewSet)
router.register('ingredients', IngredientReadOnlyModelViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
