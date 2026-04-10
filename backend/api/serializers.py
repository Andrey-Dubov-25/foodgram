import re

from rest_framework import serializers
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField


from core.utils import User
from core import constants
from recipe.models import (
    Recipe,
    Tag,
    Ingredient,
    IngredientRecipe,
    Subscribe, Favorite,
    ShoppingCard
)

class UsernameValidatorMixin:
    def validate_username(self, value):
        """Валидация поля username на допустимые символы."""
        if not re.match(r'^[\w.@+-]+\Z$', value):
            raise serializers.ValidationError(
                'Недопустимый username. Доступно только буквы, цифры и '
                'символы @/./+/-/_.'
            )
        return value


class UserSerializer(UsernameValidatorMixin, serializers.ModelSerializer):
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
        request = self.context.get('request')
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
    password = serializers.CharField(max_length=256, write_only=True)

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
        """Валидация на существование email с таким же usermname, которые
        указаны при регистрации.
        """
        username = data['username']
        email = data['email']

        username_for_user = User.objects.filter(username=username).first()
        email_for_user = User.objects.filter(email=email).first()

        if username_for_user:
            raise serializers.ValidationError(
                'Пользователь с таким username уже зарегистрирован '
                'с другим email.'
            )
        if email_for_user:
            raise serializers.ValidationError(
                'Email уже используется другим пользователем.'
            )

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class GetTokenSerializer(serializers.Serializer):
    """Сериализация данных при получении токена."""
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=256)

    def validate(self, data):
        """
        Валидация кода подтверждения на соответствие из отправленного в
        сообщении на email.
        """
        email = data['email']
        password = data['password']
        user = get_object_or_404(User, email=email)

        if not user.check_password(password):
            raise serializers.ValidationError('Неверный пароль')
        self.user = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=256)
    current_password = serializers.CharField(max_length=256)

    def validate(self, data):
        user = self.context['request'].user
        current_password = data['current_password']

        if not user.check_password(current_password):
            raise serializers.ValidationError({
                'current_password': 'Неверный текущий пароль'
            })
        return data


class UserMeSerializer(UsernameValidatorMixin, serializers.ModelSerializer):
    """
    Сериализация данных для получения информации пользователем о своей учетной
    записи.
    """
    avatar = Base64ImageField(required=False, allow_null=True)

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
    

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    def validate(self, data):

        if 'avatar' not in data:
            raise serializers.ValidationError(
                'Поле avatar обязательно для загрузки.'
            )
        return data

    class Meta:
        model = User
        fields = ('avatar',)



class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientRecipeSerializer(write_only=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author',)
        
    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Поле ингредиентов не может быть пустым!')
        return value
    
    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Поле тегов не может быть пустым!')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Нельзя добавлять одинаковые теги!')
        return value
    
    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Нельзя оставлять поле изображения пустым!')
        return value
    
    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError('Время приготовления не должно быть меньше 1!')
        return value
    
    def validate(self, data):
        if 'image' not in data:
            raise serializers.ValidationError('Необходимо добавить изображение!')
        if 'tags' not in data:
            raise serializers.ValidationError('Необходимо передать теги!')
        if 'ingredients' not in data:
            raise serializers.ValidationError('Необходимо передать ингредиенты!')
        ingredients = data.get('ingredients')
        id = []
        count = 0
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient.get('id')).exists():
                raise serializers.ValidationError('Такого ингредиента не существует!')
            id.append(ingredient.get('id'))
            count += 1
        if count != len(set(id)):
            raise serializers.ValidationError('Нельзя добавлять одинаковые ингредиенты!')
        return data
        

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCard.objects.filter(user=request.user, recipe=obj).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        ingredients = instance.ingredientrecipe_set.all()
        data['ingredients'] = []

        for ingredient in ingredients:
            ingredient_data = {
                'id': ingredient.ingredient.id,
                'name': ingredient.ingredient.name,
                'measurement_unit': ingredient.ingredient.measurement_unit,
                'amount': ingredient.amount
            }
            data['ingredients'].append(ingredient_data)

        tags = TagSerializer(instance.tags.all(), many=True).data
        data['tags'] = tags

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)

        for ingredient in ingredients:
            id = ingredient['id']
            amount = ingredient['amount']
            ingredient = Ingredient.objects.get(id=id)
            IngredientRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

        return recipe
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        tags = validated_data.get('tags')
        if tags is not None:
            instance.tags.set(tags)
        instance.save
        return instance



class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""
    subscribing = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, data):
        current_user = self.context.get('request').user
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
        request = self.context.get('request')
        subscribing = instance.subscribing

        recipes_queryset = subscribing.recipes.all()
        recipe_count = subscribing.recipes.count()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            limit = int(recipes_limit)
            if limit >= 0:
                recipes_queryset = recipes_queryset[:limit]
            

        recipe_in_data = [
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            } for recipe in recipes_queryset
        ]
        is_subscribed = Subscribe.objects.filter(user=request.user, subscribing=subscribing).exists()
        data = {
            'email': subscribing.email,
            'id': subscribing.id,
            'username': subscribing.username,
            'first_name': subscribing.first_name,
            'last_name': subscribing.last_name,
            'is_subscribed': is_subscribed,
            'recipes': recipe_in_data,
            'recipes_count': recipe_count,
            'avatar': subscribing.avatar.url if subscribing.avatar else None
        }

        return data


    class Meta:
        model = Subscribe
        fields = ('user', 'subscribing',)


class SubscribeDeleteSerializer(serializers.Serializer):
    subscribing_id = serializers.IntegerField()

    def validate_subscribing_id(self, value):
        try:
            subscribing = User.objects.get(pk=value)
            self.context['subscribing'] = subscribing
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'Такого юзера не существует!'}, code='not_found')

    def validate(self, data):
        user = self.context['request'].user
        subscribing = self.context['subscribing']

        if not Subscribe.objects.filter(user=user, subscribing=subscribing).exists():
            raise serializers.ValidationError({'Такой подписки не существует!'}, code='bad_request')

        return data


class FavoriteSerializer(serializers.ModelSerializer):
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
    
    def to_representation(self, instance):
        recipe = {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': instance.recipe.image.url if instance.recipe.image else None,
            'cooking_time': instance.recipe.cooking_time
        }
        return recipe


class FavoriteDeleteSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):
        try:
            recipe = Recipe.objects.get(pk=value)
            self.context['recipe'] = recipe
            return value
        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'Рецепт не существует!'},
                code='not_found'
            )

    def validate(self, data):
        user = self.context['request'].user
        recipe = self.context['recipe']

        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'Такого рецепта нет в избранном!'},
                code='bad_request'
            )
        return data


class ShoppingCardSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        recipe = {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': instance.recipe.image.url if instance.recipe.image else None,
            'cooking_time': instance.recipe.cooking_time
        }
        return recipe


class ShoppingCardDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления из корзины покупок."""
    recipe_id = serializers.IntegerField()

    def validate_recipe_id(self, value):
        """Проверка на существования рецепта. Если не найден - ошибка 404."""

        try:
            recipe = Recipe.objects.get(pk=value)
            self.context['recipe'] = recipe
            return value

        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'Рецепт не существует!'},
                code='not_found'
            )

    def validate(self, data):
        """
        Проверка на существование рецепта в корзине — если не найден - ошибка
        400.
        """
        user = self.context['request'].user
        recipe = self.context['recipe']

        if not ShoppingCard.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт не найден в корзине'},
                code='bad_request'
            )

        return data
