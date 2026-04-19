from io import BytesIO

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.urls import reverse

from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core import utils
from recipe.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCard,
    Subscribe,
    Tag,
    User
)
from .filters import RecipeFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    ChangePasswordSerializer,
    FavoriteDeleteSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCardDeleteSerializer,
    ShoppingCardSerializer,
    SubscribeDeleteSerializer,
    SubscribeWriteSerializer,
    SubscribeReadSerializer,
    TagSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для обработки запросов с пользователями."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    pagination_class = LimitPagination

    def get_queryset(self):
        """Возвращает пользователя со связанными с ним данными."""
        return User.objects.prefetch_related(
            'subscriptions',
            'subscribed_by',
            'recipes__tags',
            'recipes__recipe_ingredients__ingredient',
            'recipes__author'
        )

    def get_serializer_class(self, *args, **kwargs):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'avatar':
            return AvatarSerializer
        elif self.action == 'set_password':
            return ChangePasswordSerializer
        else:
            return UserSerializer

    @action(
        detail=False,
        methods=utils.get_method(),
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение пользователем своего профиля."""
        user = utils.get_user(request)
        serializer = self.get_serializer(instance=user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=utils.put_delete_methods(),
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Добавление/удаление аватара (фото профиля)."""
        user = utils.get_user(request)

        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            avatar = user.avatar

            if avatar:
                avatar.delete()
                user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=utils.post_method(),
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Смена пароля для авторизированного пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = utils.get_user(request)
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=utils.post_delete_methods(),
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Добавление/удаление подписки на пользователя."""
        user = utils.get_user(request)
        subscribe_user = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit')
            data = {
                'user': user, 'subscribing': subscribe_user.id
            }
            context = {'request': request, 'recipes_limit': recipes_limit}
            serializer = SubscribeWriteSerializer(data=data, context=context)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            data = {'subscribing_id': subscribe_user.id}
            context = utils.get_request(request)
            serializer = SubscribeDeleteSerializer(data=data, context=context)

            if serializer.is_valid():
                subscribe = get_object_or_404(
                    Subscribe, user=user, subscribing=subscribe_user
                )
                subscribe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            errors = serializer.errors

            if 'not_found' in str(errors):
                return Response(errors, status=status.HTTP_404_NOT_FOUND)

            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=utils.get_method(),
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение информации о своих подписках."""
        user = utils.get_user(request)
        recipes_limit = request.query_params.get('recipes_limit')
        subscriptions = Subscribe.objects.filter(user=user).select_related(
            'subscribing'
        ).prefetch_related('subscribing__recipes')
        page = self.paginate_queryset(subscriptions)
        users = [user_sub.subscribing for user_sub in page]
        context = {'request': request, 'recipes_limit': recipes_limit}
        serializer = SubscribeReadSerializer(users, many=True, context=context)
        return self.get_paginated_response(serializer.data)


class RecipeList(viewsets.ModelViewSet):
    """Вьюсет для обработки запросов с рецептами."""

    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagination
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_queryset(self):
        """Получение списка рецептов в завизимости от наличия параметров."""
        return Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags',
            'ingredients',
            'recipe_ingredients__ingredient',
            'favorites_by',
            'in_shopping_card'
        )

    def get_serializer_class(self, *args, **kwargs):
        """Возвращает сериализатор в зависимости от чтения или записи."""
        if self.action in utils.list_retrieve_methods():
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        """Доступ на редактирование только автору рецепта."""
        if self.action in ['list', 'retrieve']:
            return (AllowAny(),)

        elif self.action == 'create':
            return (IsAuthenticated(),)

        else:
            return (IsAuthorOrReadOnly(),)

    def perform_create(self, serializer):
        """Присваивание автора рецепта текущего пользователя."""
        serializer.save(author=utils.get_self_user(self))

    @action(
        detail=True,
        methods=utils.post_method(),
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецептов в избранное."""
        return self.method_for_post(
            request=request,
            pk=pk,
            serializer_for_model=FavoriteSerializer,
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецептов из избранного."""
        return self.method_for_delete(
            request=request,
            pk=pk,
            model=Favorite,
            serializer_for_model=FavoriteDeleteSerializer,
        )

    @action(
        detail=True,
        methods=utils.post_method(),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецептов в список покупок."""
        return self.method_for_post(
            request=request,
            pk=pk,
            serializer_for_model=ShoppingCardSerializer,
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаление рецептов из списка покупок."""
        return self.method_for_delete(
            request=request,
            pk=pk,
            model=ShoppingCard,
            serializer_for_model=ShoppingCardDeleteSerializer,
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Генерация короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_url = request.build_absolute_uri(f'/s/{recipe.short_link}/')
        return Response({'short-link': short_url})

    @action(
        detail=False,
        methods=utils.get_method(),
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание ингредиентов из списка покупок."""
        user = utils.get_user(request)

        shopping_card = ShoppingCard.objects.filter(user=user).values(
            name=F('recipe__recipe_ingredients__ingredient__name'),
            measurement_unit=F(
                'recipe__recipe_ingredients__ingredient__measurement_unit'
            )
        ).annotate(total=Sum('recipe__recipe_ingredients__amount')).order_by(
            'name'
        )

        if not shopping_card:
            return Response('Корзина покупок пуста!')

        data = [
            {
                'name': ingredient['name'],
                'total': ingredient['total'],
                'unit': ingredient['measurement_unit']
            }
            for ingredient in shopping_card
        ]

        file_data = self.ingredients_to_text(data)

        response = HttpResponse(
            file_data, content_type='text/plain; charset=utf-8'
        )

        return response

    @staticmethod
    def ingredients_to_text(ingredients):
        """Получение текстового файла с ингредиентами."""
        text_to_print = 'Нужно купить:\n'
        text_to_print += '\n'.join(
            f"{el['name']}: {el['total']} {el['unit']} "
            for el in ingredients
        )
        return BytesIO(text_to_print.encode('utf-8'))

    @staticmethod
    def method_for_post(request, pk, serializer_for_model):
        """Функция для создания объектов."""
        context = utils.get_request(request)
        data = utils.get_recipe_id(pk)
        get_object_or_404(
            Recipe.objects.select_related('author'),
            pk=pk
        )
        serializer = serializer_for_model(data=data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def method_for_delete(request, pk, model, serializer_for_model):
        """Функция для удаления объектов."""
        user = utils.get_user(request)
        context = utils.get_request(request)
        data = utils.get_recipe_id(pk)
        serializer = serializer_for_model(data=data, context=context)

        if serializer.is_valid():
            recipe = serializer.context['recipe']
            model_obj = get_object_or_404(
                model, user=user, recipe=recipe
            )
            model_obj.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        errors = serializer.errors

        if 'not_found' in str(errors):
            return Response(errors, status=status.HTTP_404_NOT_FOUND)

        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)

# class ShortLinkView(View):
#     """Получение рецепта по короткой ссылке."""

#     def get(self, request, short_link):
#         """Возвращает страницу рецепт по короткой ссылке."""
#         recipe = get_object_or_404(Recipe, short_link=short_link)
#         recipe_id = recipe.id
#         url = reverse('recipe-detail', kwargs={'pk': recipe_id})
#         return redirect(url)
class ShortLinkView(View):
    """Получение рецепта по короткой ссылке."""

    def get(self, request, short_link):
        """Возвращает страницу рецепт по короткой ссылке."""
        recipe = get_object_or_404(Recipe, short_link=short_link)
        recipe_id = recipe.id
        return redirect(f'/recipes/{recipe_id}')
