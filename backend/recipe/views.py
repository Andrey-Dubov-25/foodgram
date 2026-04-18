from django.shortcuts import redirect


def recipe_for_short_link(request, pk):
    """Возвращает страницу рецепта по короткой ссылке."""
    return redirect('recipe-detail', pk=pk)
