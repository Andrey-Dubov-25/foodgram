# from django.shortcuts import get_object_or_404, redirect

# from .models import Recipe


# def redirect_short_link(request, short_link):
#     """Перенаправление по короткой ссылке на рецепт."""
#     recipe = get_object_or_404(Recipe, short_link=short_link)
#     return redirect(f'/recipes/{recipe.pk}/')
