from django_filters.rest_framework import (
    FilterSet, ModelMultipleChoiceFilter, BooleanFilter, CharFilter
)

from recipes.models import Recipe, Ingredient, Tag


class RecipeFilter(FilterSet):
    is_in_shopping_cart = BooleanFilter(
        method='recipe_in_shopping_cart_filter'
    )
    is_favorite = BooleanFilter(
        method='is_favorite_filter'
    )
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        conjoined=False
    )

    def recipe_in_shopping_cart_filter(self, name, queryset, pk):
        if pk:
            user = self.request.user
            return queryset.filter(shopping_recipe__user_id=user.id)
        return queryset

    def is_favorite_filter(self, name, queryset, pk):
        if pk:
            user = self.request.user
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('is_favorite', 'tags', 'is_in_shopping_cart', 'author')


class IngridientFilter(FilterSet):
    name = CharFilter(
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
