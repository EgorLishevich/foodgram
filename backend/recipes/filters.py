from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet,
                                           ModelMultipleChoiceFilter)

from .models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    is_in_shopping_cart = BooleanFilter(
        method='recipe_in_shopping_cart_filter'
    )
    is_favorited = BooleanFilter(
        method='is_favorite_filter'
    )
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        conjoined=False
    )

    def recipe_in_shopping_cart_filter(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(shopping_cart__user_id=user.id)
        return queryset

    def is_favorite_filter(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'tags', 'is_in_shopping_cart', 'author')


class IngridientFilter(FilterSet):
    name = CharFilter(
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
