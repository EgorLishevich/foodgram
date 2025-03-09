from api.fields import Base64ImageField
from api.serializer import UserProfileSerializer
from rest_framework import serializers

from .models import (Favorite, Ingredient, IngridientsInRecipe, Recipe,
                     ShoppingCart, Tag)


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

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
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
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value

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
        for ingredient_data in value:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            if not ingredient_id or not amount:
                raise serializers.ValidationError(
                    'Укажите ID и количество ингредиента'
                )
            if amount <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0'
                )
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
        user = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags',)
        IngridientsInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, validated_data.pop('ingredients'))

        if tags_data is not None:
            instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        ingredient_instances = []
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            ingredient_instances.append(
                IngridientsInRecipe(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            )
        IngridientsInRecipe.objects.bulk_create(ingredient_instances)


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

    def validate(self, data):
        action = self.context.get('action')
        if action == 'shopping_cart':
            pass
        return super().validate(data)


class FavoriteSerializer(UserRecipeSerializer, serializers.ModelSerializer):
    class Meta(UserRecipeSerializer.Meta):
        model = Favorite

    def validate(self, data):
        action = self.context.get('action')
        if action == 'favorites':
            pass
        return super().validate(data)
