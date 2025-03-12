from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class UsersAdmin(UserAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'email', 'avatar', 
        'subscribers_count', 'recipes_count', 'pk'
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')

    @admin.display(description='Колл-во подписчикоа')
    def subscribers_count(self, obj):
        return obj.subscription_author.count()

    @admin.display(description='Колл-во рецептов')
    def recipes_count(self, obj):
        return obj.authored_recipes.count()
