from django.urls import path

from .views import redirect_short_link

urlpatterns = [
    path(
        's/<str:short_link>/',
        redirect_short_link,
        name='redirect_short_link',
    ),
]