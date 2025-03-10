import hashids
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorite, Ingredient, IngredientsInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User
from .pagination import PagePagination
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from .serializer import (CreateRecipeSerializer, CreateSubscriptionSerializer,
                         FavoriteSerializer, RecipeSerializer,
                         ShoppingCartSerializer, ShortIngredientsSerializer,
                         SubscriptionSerializer, TagSerializer,
                         UserAvatarSerializer, UserProfileSerializer)


class UserProfileViewSet(UserViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination
    queryset = User.objects.all()

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='me'
    )
    def me(self, request):
        serializer = UserProfileSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscription_author__subscriber=request.user
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['delete', 'put'],
        permission_classes=[IsAuthenticated],
        detail=True,
        url_path='avatar'
    )
    def create_avatar(self, request, id):
        serializer = UserAvatarSerializer(
            request.user, partial=True, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)

    def delete_avatar(self, request, id):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        if request.method == 'POST':
            return self.create_subscription(request, id)
        return self.delete_subscription(request, id)

    def delete_subscription(self, request, id):
        subs = Subscription.objects.filter(
            subscriber=request.user.id, author=id
        )

        author = User.objects.get(pk=id)
        if not subs.exists():
            return Response(
                f'Вы не подписаны на {author}',
                status=HTTP_400_BAD_REQUEST,
            )

        subs.delete()

        return Response(
            status=HTTP_204_NO_CONTENT
        )

    def create_subscription(self, request, id):
        serializer = CreateSubscriptionSerializer(
            data={
                'subscriber': request.user.id,
                'author': id,
            },
            context={'request': request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=HTTP_201_CREATED)


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
            IngredientsInRecipe.objects.filter(
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
        recipe = self.get_object()
        hashid = hashids.Hashids(salt='random_salt', min_length=6)
        hashid_id = hashid.encode(recipe.id)
        short_link = f'{request.get_host()}/s/{hashid_id}'
        return Response({'short-link': short_link})


def redirect_to_recipe(request, short_id):
    hashid = hashids.Hashids(salt='random_salt', min_length=6)
    decoded_id = hashid.decode(short_id)
    if decoded_id:
        recipe_id = decoded_id[0]
        return redirect(f'/recipes/{recipe_id}/')
    return HttpResponseNotFound('Рецепт не был найден')


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ShortIngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    pagination_class = None
