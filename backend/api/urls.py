from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet
from recipes.views import (
    IngredientViewSet, TagViewSet, RecipeViewSet
)


router = routers.DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("tags", TagViewSet, basename="tags")
router.register("users", UserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")

name_app = "api"

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
