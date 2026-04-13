from collections import defaultdict
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
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
)
from .filters import RecipeFilter
from .permissions import AuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    ChangePasswordSerializer,
    FavoriteDeleteSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCardDeleteSerializer,
    ShoppingCardSerializer,
    SubscribeDeleteSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для обработки запросов с пользователями."""
    queryset = utils.User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination

    def create(self, request, *args, **kwargs):
        """Создание польователя."""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=utils.get_method(),
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """
        Получение пользователем своего профиля. Доступно только
        аутентифицированным пользователям.
        """
        user = utils.get_user(request)
        serializer = self.get_serializer(instance=user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=utils.put_delete_methods(),
        url_path='me/avatar',
        serializer_class=AvatarSerializer,
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
        serializer_class=ChangePasswordSerializer,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """
        Смена пароля для авторизированного пользователя. Необходимо указать
        текущий пароль и новый.
        """
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
        subscribe_user = get_object_or_404(utils.User, pk=pk)

        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit')
            data = {
                'user': user, 'subscribing': subscribe_user.id
            }
            context = {'request': request, 'recipes_limit': recipes_limit}
            serializer = SubscribeSerializer(data=data, context=context)

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
        subscriptions = Subscribe.objects.filter(user=user).select_related(
            'subscribing'
        ).prefetch_related('subscribing__recipes')
        page = self.paginate_queryset(subscriptions)
        serializer = SubscribeSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeList(viewsets.ModelViewSet):
    """Вьюсет для обработки запросов с рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_queryset(self):
        """
        Получение списка рецептов в завизимости от наличия в списке покупок или
        в избранном.
        """

        queryset = super().get_queryset().prefetch_related(
            'tags',
            'ingredientrecipe_set__ingredient'
        )
        user = utils.get_self_user(self)
        is_in_card = self.request.query_params.get('is_in_shopping_cart')
        is_in_favorite = self.request.query_params.get('is_favorited')

        if not user.is_authenticated:
            if is_in_card == '1' or is_in_favorite == '1':
                return queryset

        if is_in_card is None and is_in_favorite is None:
            return queryset

        if is_in_card == str(1):
            cart_recipe = ShoppingCard.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            queryset = queryset.filter(id__in=cart_recipe)

        elif is_in_favorite == str(1):
            favorite_recipe = Favorite.objects.filter(
                user=user
            ).values_list('recipe_id', flat=True)
            queryset = queryset.filter(id__in=favorite_recipe)

        return queryset.distinct()


    def get_permissions(self):
        """Доступ на редактирование только автору рецепта."""
        if self.action in ['list', 'retrieve']:
            return (AllowAny(),)
        elif self.action == 'create':
            return (IsAuthenticated(),)
        else:
            return (AuthorOrReadOnly(),) 

    def perform_create(self, serializer):
        """Присваивание автора рецепта текущего пользователя"""
        serializer.save(author=utils.get_self_user(self))
    
    @action(
        detail=True,
        methods=utils.post_delete_methods(),
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецептов в избранное."""
        user = utils.get_user(request)
        data = utils.get_recipe_id(pk)
        context = utils.get_request(request)

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            serializer = FavoriteSerializer(data=data, context=context)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            serializer = FavoriteDeleteSerializer(data=data, context=context)

            if serializer.is_valid():
                recipe = serializer.context['recipe']
                favorite = get_object_or_404(
                    Favorite, user=user, recipe=recipe
                )
                favorite.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

            errors = serializer.errors

            if 'not_found' in str(errors):
                return Response(errors, status=status.HTTP_404_NOT_FOUND)

            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=utils.post_delete_methods(),
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецептов в список покупок."""
        user = utils.get_user(request)
        data = utils.get_recipe_id(pk)
        context = utils.get_request(request)

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            serializer = ShoppingCardSerializer(data=data, context=context)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'DELETE':
            serializer = ShoppingCardDeleteSerializer(
                data=data, context=context
            )

            if serializer.is_valid():
                recipe = serializer.context['recipe']
                favorite = get_object_or_404(
                    ShoppingCard, user=user, recipe=recipe
                )
                favorite.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

            errors = serializer.errors

            if 'not_found' in str(errors):
                return Response(errors, status=status.HTTP_404_NOT_FOUND)

            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_code = str(recipe.pk)
        relative_path = f'/api/recipes/{short_code}/'
        short_url = request.build_absolute_uri(relative_path)
        return Response({'short-link': short_url})

    @action(
        detail=False,
        methods=utils.get_method(),
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание ингредиентов из списка покупок."""
        user = utils.get_user(request)

        shopping_card_for_user = ShoppingCard.objects.filter(
            user=user
        ).select_related('recipe')

        recipes = [item.recipe for item in shopping_card_for_user]

        if not recipes:
            return Response('Корзина покупок пуста!')
        
        ingredients = defaultdict(int)

        for recipe in recipes:
            for ingredient_recipe in recipe.ingredientrecipe_set.all():
                ingredient = ingredient_recipe.ingredient
                key = (ingredient.name, ingredient.measurement_unit)
                ingredients[key] += ingredient_recipe.amount

        text_to_print = 'список покупок:\n\n'

        sorted_items = sorted(ingredients.items(), key=lambda x: x[0][0])

        for (name, unit), total in sorted_items:
            text_to_print += f'{name}: {total} {unit}\n'

        data = [
            {'name': name, 'total': total, 'unit': unit}
            for (name, unit), total in ingredients.items()
        ]

        file_data = self.ingredients_to_text(data)

        response = HttpResponse(
            file_data, content_type='text/plain; charset=utf-8'
        )
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'

        return response

    @staticmethod
    def ingredients_to_text(ingredients):
        """Получение текстового файла с ингредиентами."""
        text_to_print = 'Нужно купить:\n'
        text_to_print += '\n'.join(
            f'{item['name']}: {item['total']} {item['unit']} '
            for item in ingredients
        )

        return BytesIO(text_to_print.encode('utf-8'))

class TagReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class IngredientReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)
