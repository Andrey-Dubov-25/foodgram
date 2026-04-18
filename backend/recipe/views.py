from django.shortcuts import redirect

from .models import Recipe


def redirect_short_link(request, short_link):
    """Перенаправление по короткой ссылке на рецепт."""
    try:
        recipe = Recipe.objects.get(short_link=short_link)
        return redirect(f'/recipes/{recipe.pk}/')
    except Recipe.DoesNotExist:
        return redirect('/404/')