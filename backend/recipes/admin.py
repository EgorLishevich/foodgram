from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from recipes.models import (
    Ingredient, IngridientsInRecipe, Recipe,
    ShoppingCart, Favorite, Tag
)
from users.models import Subscription
from foodgram.consts import INGREDIENT_INLINE_MIN_AMOUNT


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('pk', 'recipe', 'user')


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('pk', 'recipe', 'user')


@register(Subscription)
class SubscribtionAdmin(ModelAdmin):
    list_display = ('pk', 'author', 'subscriber')
    search_fields = ('subscriber__username', 'author__username')
    list_filter = ('author', 'subscriber')


@register(Ingredient)
class IngridientAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)


class IngredientInRecipeAdmin(admin.TabularInline):  # Правильный класс для inlines
    model = IngridientsInRecipe
    min_num = INGREDIENT_INLINE_MIN_AMOUNT


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('pk', 'slug', 'name')


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'pk', 'author', 'name', 'created', 'get_favorites', 'get_tags'
    )
    list_filter = ('author', 'name', 'tags')
    search_fields = ('author__username', 'name')
    inlines = [IngredientInRecipeAdmin]  # Используем правильный класс

    @admin.display(description='Кол-во рецептов в избранном')
    def get_favorites(self, object):
        return object.favorites.count()

    @admin.display(description='Теги')
    def get_tags(self, object):
        return '\n'.join(object.tags.values_list('name', flat=True))
