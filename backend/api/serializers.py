from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.conf import settings

from core import constants, utils
from recipe.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCard,
    Subscribe,
    Tag,
    User
)
from .mixins import (
    RecipeDeleteFromMixin,
    RecipeRepresentationMixin,
    UsernameValidatorMixin,
)


class UserSerializer(UsernameValidatorMixin, serializers.ModelSerializer):
    """Сериализация данных пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        """Возвращает булевое значение о подписке на позьзователя."""
        request = utils.get_context_request(self)

        if not request or not request.user.is_authenticated:
            return False

        return Subscribe.objects.filter(
            user=request.user, subscribing=obj
        ).exists()


class UserRegistrationSerializer(
    UsernameValidatorMixin, serializers.ModelSerializer
):
    """Сериализация данных при регистрации пользователя."""

    email = serializers.EmailField(max_length=constants.EMAIL_LEN)
    username = serializers.CharField(max_length=constants.USERNAME_LEN)
    first_name = serializers.CharField(max_length=constants.FIRST_NAME_LEN)
    last_name = serializers.CharField(max_length=constants.LAST_NAME_LEN)
    password = serializers.CharField(
        max_length=constants.PASSWORD_LEN, write_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate(self, data):
        """Валидация на существование email или usermname, которые указаны при
        регистрации.
        """
        username = utils.get_username(data)
        email = utils.get_email(data)
        username_for_user = User.objects.filter(
            username=username
        ).first()
        email_for_user = User.objects.filter(email=email).first()

        if username_for_user:
            raise serializers.ValidationError(
                'Пользователь с таким username уже зарегистрирован.'
            )
        if email_for_user:
            raise serializers.ValidationError(
                'Email уже используется другим пользователем.'
            )

        return data

    def create(self, validated_data):
        """Регистрация пользователя."""
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class GetTokenSerializer(serializers.Serializer):
    """Сериализация данных при получении токена."""

    email = serializers.EmailField(max_length=constants.EMAIL_LEN)
    password = serializers.CharField(max_length=constants.PASSWORD_LEN)

    def validate(self, data):
        """Валидация пароля на соответствие с указанным при регистрации."""
        email = utils.get_email(data)
        password = utils.get_password(data)
        user = get_object_or_404(User, email=email)

        if not user.check_password(password):
            raise serializers.ValidationError('Неверный пароль')

        self.user = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализация данных при смене пароля."""

    new_password = serializers.CharField(max_length=constants.PASSWORD_LEN)
    current_password = serializers.CharField(max_length=constants.PASSWORD_LEN)

    def validate(self, data):
        """Валидация пароля на соответствие с указанным при регистрации."""
        user = self.context['request'].user
        current_password = data['current_password']

        if not user.check_password(current_password):
            raise serializers.ValidationError('Неверный пароль')

        return data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализация при обработке поля avatar."""

    avatar = Base64ImageField()

    def validate(self, data):
        """Валидация на наличие поля avatar."""
        if 'avatar' not in data:
            raise serializers.ValidationError(
                'Поле avatar обязательно для загрузки.'
            )

        return data

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализация ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов."""

    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализация тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""
    image = Base64ImageField()
    ingredients = IngredientRecipeReadSerializer(
        source='recipe_ingredients', many=True
    )
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Возвращает булевое значение о наличии рецепта в избранном."""
        request = utils.get_context_request(self)

        if not request or not request.user.is_authenticated:
            return False

        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Возвращает булевое значение о наличии рецепта в списке покупок."""
        request = utils.get_context_request(self)

        if not request or not request.user.is_authenticated:
            return False

        return ShoppingCard.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализация рецептов."""

    image = Base64ImageField()
    ingredients = IngredientWriteSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def to_representation(self, instance):
        """Возвращает рецепт в расширенном представлении."""
        serializer = RecipeReadSerializer(instance)
        return serializer.data

    def validate_ingredients(self, value):
        """Валидация на наличие ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Поле ингредиентов не может быть пустым!'
            )

        return value

    def validate_tags(self, value):
        """Валидация на наличие тегов и их повторение."""
        if not value:
            raise serializers.ValidationError(
                'Поле тегов не может быть пустым.'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Нельзя добавлять одинаковые теги.'
            )

        return value

    def validate_image(self, value):
        """Валидация на наличие изображения."""
        if not value:
            raise serializers.ValidationError(
                'Нельзя оставлять поле изображения пустым!'
            )

        return value

    def validate_cooking_time(self, value):
        """Валидация времени приготовления."""
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не должно быть меньше 1!'
            )

        return value

    def validate(self, data):
        """Валидация на наличие полей tags и ingredients."""
        if 'tags' not in data:
            raise serializers.ValidationError('Необходимо добавить tags.')
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'Необходимо добавить ingredients.'
            )

        ingredients = data.get('ingredients')
        id = []
        count = 0

        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient.get('id')).exists():
                raise serializers.ValidationError(
                    'Такого ингредиента не существует!'
                )

            id.append(ingredient.get('id'))
            count += 1

        if count != len(set(id)):
            raise serializers.ValidationError(
                'Нельзя добавлять одинаковые ингредиенты!'
            )

        return data

    def create(self, validated_data):
        """Создает рецепт с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe=recipe, ingredients=ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт с возможность изменения тегов и ингредиентов."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            IngredientRecipe.objects.filter(recipe=instance).delete()
            self.add_ingredients(recipe=instance, ingredients=ingredients)
        instance.save()
        return instance

    @staticmethod
    def add_ingredients(recipe, ingredients):
        """Добавление ингредиентов к рецепту."""
        all_ingredients = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            amount = ingredient['amount']
            new_ingredient = IngredientRecipe(
                ingredient_id=ingredient_id,
                recipe=recipe,
                amount=amount
            )
            all_ingredients.append(new_ingredient)
        IngredientRecipe.objects.bulk_create(all_ingredients)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов пользователя."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для расширенного представления подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        """Возвращает булевое значение о подписке на позьзователя."""
        request = utils.get_context_request(self)

        if not request or not request.user.is_authenticated:
            return False

        return Subscribe.objects.filter(
            user=request.user, subscribing=obj
        ).exists()

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя."""
        request = utils.get_context_request(self)
        recipes_queryset = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            limit = int(recipes_limit)

            if limit >= 0:
                recipes_queryset = recipes_queryset[:limit]

        serializer = RecipeShortSerializer(recipes_queryset, many=True)
        return serializer.data


class SubscribeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    subscribing = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscribe
        fields = ('user', 'subscribing',)

    def validate(self, data):
        """Валидация подписки на самого себя или повторной подписки."""
        current_user = utils.get_context_request(self).user
        subscribing = data.get('subscribing')

        if current_user == subscribing:
            raise serializers.ValidationError(
                'Нельзя оформить подписку на самого себя!'
            )

        if Subscribe.objects.filter(
            user=current_user, subscribing=subscribing
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )

        return data

    def to_representation(self, instance):
        """
        Возвращает расширенное представление о пользователе, на которого
        подписываются. Можно добавить фильтрацию по recipes_limit - количестве
        выводимых рецептов у пользователя.
        """
        subscribing = instance.subscribing
        serializers = SubscribeReadSerializer(
            subscribing, context=self.context
        )
        return serializers.data


class SubscribeDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления подписки."""

    subscribing_id = serializers.IntegerField()

    def validate_subscribing_id(self, value):
        """Валидация на существование пользователя для подписки."""
        try:
            subscribing = User.objects.get(pk=value)
            self.context['subscribing'] = subscribing
            return value

        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'Такого юзера не существует!'},
                code='not_found'
            )

    def validate(self, data):
        """Валидация существования подписки."""
        user = self.context['request'].user
        subscribing = self.context['subscribing']

        if not Subscribe.objects.filter(
            user=user, subscribing=subscribing
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Такой подписки не существует!'},
                code='bad_request'
            )

        return data


class FavoriteSerializer(
    RecipeRepresentationMixin, serializers.ModelSerializer
):
    """Сериализатор для списка избранного."""

    recipe_id = serializers.IntegerField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Favorite
        fields = ('recipe_id', 'user')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe_id'],
                message='Рецепт уже в избранном!'
            )
        ]


class FavoriteDeleteSerializer(
    RecipeDeleteFromMixin, serializers.Serializer
):
    """Сериализатор для удаления из корзины покупок."""

    recipe_id = serializers.IntegerField()
    relation_model = Favorite

    def get_error_message(self):
        """Возвращает сообщение об ошибке."""
        return 'Рецепт не найден в избранном.'


class ShoppingCardSerializer(
    RecipeRepresentationMixin, serializers.ModelSerializer
):
    """Сериализатор для списка списка покупок."""

    recipe_id = serializers.IntegerField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ShoppingCard
        fields = ('recipe_id', 'user')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCard.objects.all(),
                fields=['user', 'recipe_id'],
                message='Рецепт уже в корзине!'
            )
        ]


class ShoppingCardDeleteSerializer(
    RecipeDeleteFromMixin, serializers.Serializer
):
    """Сериализатор для удаления из корзины покупок."""

    recipe_id = serializers.IntegerField()
    relation_model = ShoppingCard

    def get_error_message(self):
        """Возвращает сообщение об ошибке."""
        return 'Рецепт не найден в списке покупок.'

class RecipeShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['short_link']

    def get_short_link(self, obj):
        base_url = getattr(settings, 'BASE_URL', 'https://foodgram.serveblog.net')
        return f'{base_url}/s/{obj.short_link}'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {'short-link': data['short_link']}