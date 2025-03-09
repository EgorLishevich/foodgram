from api.pagination import PagePagination
from api.permissions import IsAuthorOrReadOnly
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import IngridientFilter, RecipeFilter
from .models import (Favorite, Ingredient, IngridientsInRecipe, Recipe,
                     ShoppingCart, Tag)
from .serializer import (CreateRecipeSerializer, FavoriteSerializer,
                         RecipeSerializer, ShoppingCartSerializer,
                         ShortIngredientsSerializer, TagSerializer)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PagePagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        serializer_classes = {
            'create': CreateRecipeSerializer,
            'partial_update': CreateRecipeSerializer,
        }
        return serializer_classes.get(self.action, RecipeSerializer)

    def get_queryset(self):
        if self.action == 'list' and self.request.query_params.get(
            'is_favorite'
        ):
            user = self.request.user
            return super().get_queryset().filter(favorites__user=user)
        return super().get_queryset()

    def handle_user_recipe_relation(
            self, request, pk, serialier_class,
            related_name, exeption, error_massege
    ):
        if request.method == 'POST':
            serializer = serialier_class(
                data={
                    'user': request.user.id,
                    'recipe': pk
                },
                context={'action': related_name}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        try:
            getattr(
                request.user, related_name
            ).get(
                user=request.user, recipe_id=pk
            ).delete()
        except exeption:
            return Response(error_massege, status=HTTP_400_BAD_REQUEST)
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        methods=['delete', 'post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk):
        return self.handle_user_recipe_relation(
            request, pk, FavoriteSerializer, 'favorites',
            Favorite.DoesNotExist, 'Рецепт не в избранном'
        )

    @action(
        methods=['delete', 'post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.handle_user_recipe_relation(
            request, pk, ShoppingCartSerializer, 'shopping_cart',
            ShoppingCart.DoesNotExist, 'Рецепт не в списке покупок'
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingr = (
            IngridientsInRecipe.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name', 'ingredient__measurement_unit'
            ).annotate(sum=Sum('amount'))
        )
        shopping_list = "\n".join(
            f"{ingredient['ingredient__name']} = {ingredient['sum']} "
            f"{ingredient['ingredient__measurement_unit']}"
            for ingredient in ingr
        )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="Список покупок.txt"'
        )
        return response

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[IsAuthenticatedOrReadOnly],
        url_path='get-link'
    )
    def get_link(self, request, pk):
        inst = self.get_object()
        url = f"{request.get_host()}/s/{inst.id}"
        return Response(data={'short-link': url})


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ShortIngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngridientFilter
    search_fields = ('^name',)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    pagination_class = None
