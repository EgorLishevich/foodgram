from django.contrib import admin

from .models import (
    Favorite, Follow, Ingredient, IngredientRecipe, Recipe, ShoppingCart, Tag,
)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('author',)
    search_fields = ('user',)


class IngredientsInline(admin.TabularInline):
    model = IngredientRecipe


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author',)
    search_fields = ('author',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('author', 'recipe')
    list_filter = ('author',)
    search_fields = ('author',)


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    list_filter = ('recipe', 'ingredient')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name', 'pub_date',)
    search_fields = ('name',)
    list_filter = ('pub_date', 'author', 'name', 'tags')
    filter_horizontal = ('ingredients',)
    empty_value_display = 'Пусто'
    inlines = [IngredientsInline]


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug',)
    list_filter = ('name',)
    search_fields = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientRecipe, IngredientRecipeAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
