from django.urls import path

from .views import recipe_for_short_link


urlpatterns = [
    path('<int:pk>/', recipe_for_short_link, name='short_link'),
]
