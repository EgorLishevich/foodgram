from djoser.serializers import UserCreateSerializer
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User

MAX_VALUE = 32000
MIN_VALUE = 1


class UserProfileSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, data):
        user = self.context['request'].user

        return (
            user.is_authenticated and user.subscription_subscriber.filter(
                author=data.id
            ).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = ['avatar']

    def validate(self, attrs):
        avatar = self.initial_data.get('avatar')
        if not avatar:
            raise serializers.ValidationError('Аватар обязателен')

        return attrs


class CreateUserProfileSerializer(UserProfileSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'password', 'id', 'email'
        )
        extra_kwargs = {'password': {'write_only': True}}


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    recipes = serializers.ReadOnlyField(source='author.recipes.all')

    class Meta:
        model = Subscription
        fields = (
            'subscriber', 'recipes', 'author', 'recipes_count'
        )
        extra_kwargs = {
            'author': {'write_only': True},
            'subscriber': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['subscriber'] == attrs['author']:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )

        return attrs

    def to_representation(self, instance):
        pk = UserProfileSerializer(
            instance.author, context={'request': self.context['request']}
        ).data
        pk.update(super().to_representation(instance))
        return pk


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name')


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    id = serializers.IntegerField(source='ingredient.id')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('name', 'id', 'amount', 'measurement_unit')


class ShortIngredientsSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    id = serializers.IntegerField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = ('name', 'id', 'measurement_unit')


class SubscriptionSerializer(UserProfileSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'avatar', 'is_subscribed', 'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.authored_recipes.count()

    def get_recipes(self, obj):
        request = self.context['request']
        recipes = obj.authored_recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return ShortRecipeSertializer(
            recipes, many=True, context={'request': request}
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(
        source='recipe_with_ingredients',
        many=True
    )
    author = UserProfileSerializer()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'author', 'id', 'name', 'image', 'text', 'ingredients',
            'is_favorited', 'cooking_time', 'is_in_shopping_cart',
            'tags'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data

        return representation

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        if request and request.user.is_authenticated:
            return request.user.shopping_cart.filter(recipe=obj).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.favorites.filter(recipe=obj).exists()
        return False


class CreateShortIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_VALUE), MaxValueValidator(MAX_VALUE)
        ]
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')

    def validate_id(self, value):
        try:
            Ingredient.objects.get(id=value)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                f'Ингредиент с id {value} не существует'
            )
        return value


class ShortRecipeSertializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('name', 'id', 'image', 'cooking_time')


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = CreateShortIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_VALUE), MaxValueValidator(MAX_VALUE)
        ]
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'image', 'ingredients',
            'cooking_time', 'tags', 'id'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты обязательны')
        ingredients = []
        ingredient_ids = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            if not ingredient_id or not amount:
                raise serializers.ValidationError(
                    'Укажите ID и количество ингредиента'
                )
            ingredient_ids.add(ingredient_id)
            ingredients.append({'id': ingredient_id, 'amount': amount})
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Список тегов не может быть пустым'
            )

        tags_ids = [tag.id for tag in tags]
        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError(
                'В списке не могут быть одинаковые теги'
            )

        return tags

    def create(self, validated_data):
        user = self.context['request'].user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags',)
        IngredientsInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, validated_data.pop('ingredients'))

        if tags_data is not None:
            instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        ingredient_instances = []
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            ingredient_instances.append(
                IngredientsInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            )
        IngredientsInRecipe.objects.bulk_create(ingredient_instances)


class UserRecipeSerializer:

    class Meta:
        fields = ('recipe', 'user')

    def to_representation(self, inst):
        serializer = ShortRecipeSertializer(inst.recipe)
        return serializer.data


class ShoppingCartSerializer(
    UserRecipeSerializer, serializers.ModelSerializer
):
    class Meta(UserRecipeSerializer.Meta):
        model = ShoppingCart


class FavoriteSerializer(UserRecipeSerializer, serializers.ModelSerializer):
    class Meta(UserRecipeSerializer.Meta):
        model = Favorite
