from rest_framework import serializers

from api.serializer import UserProfileSerializer
from api.fields import Base64ImageField
from .models import (
    Ingredient, IngridientsInRecipe, Favorite, ShoppingCart, Recipe, Tag
)


class ShortIngredientsSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    id = serializers.IntegerField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = ('name', 'id', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name')


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'id', 'amount', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(
        source='ingredients_in_recipe'
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

    def get_is_in_shopping_cart(self, data):
        request = self.context.get('request')

        return (
            request is not None and request.user.is_authenticated
            and request.user.favorites.filter(pk=data.id).exists()
        )

    def get_is_favorited(self, data):
        request = self.context.get('request')

        return (
            request is not None and request.user.is_authenticated
            and request.user.favorites.filter(pk=data.id).exists()
        )


class CreateShortIngredientsSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()
    id = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('amount', 'id')

    def validate_amount(self, pk):
        if pk < 1:
            raise serializers.ValidationError(
                'Число ингредиента должно быть больше 1'
            )
        return pk

    def valiadte_id(self, id):
        try:
            Ingredient.objects.get(id=id)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                f'Ингридиент id которого {id} не существует'
            )
        return id


class ShortRecipeSertializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('name', 'id', 'image', 'cooking_time')


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField
    ingredients = CreateShortIngredientsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'name', 'text', 'image', 'ingredients', 'cooking_time'
        )

    def validate_ingredients(self, attrs):
        ingredients = attrs.get('ingredients')

        if not ingredients:
            raise serializers.ValidationError(
                'В списке обязателен хотя бы один ингредиент'
            )
        ingredients_id = [pk['id'] for pk in ingredients]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                'Ингредиенты в списке должны быть уникальными'
            )

        return attrs

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Список тегов не может быть пустым')
        
        tags_ids = [tag.id for tag in tags]
        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError(
                'В списке не могут быть одинаковые теги'
            )
        
        return tags

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def create(self, validated_data):
        user = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredient(ingredients, recipe)
        recipe.tags.set(tags)

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        IngridientsInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredient(validated_data.pop('ingredients'), instance)

        if tags_data is not None:
            instance.tags.set(tags_data)

        return super().update(instance, validated_data)

    def create_ingredients(self, recipe, ingredients):
        inst = []
        for pk in ingredients:
            id = pk['id']
            amount = pk['amount']

            inst.append(
                IngridientsInRecipe(
                    id=id, recipe=recipe, amount=amount
                )
            )

        IngridientsInRecipe.objects.bulk_create(inst)


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
        return super().validate(data, 'shopping_carts')


class FavoriteSerializer(
    UserRecipeSerializer, serializers.ModelSerializer
):
    class Meta(UserRecipeSerializer.Meta):
        model = Favorite

    def validate(self, data):
        return super().validate(data, 'favorites')
