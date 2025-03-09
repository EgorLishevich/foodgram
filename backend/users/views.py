from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)

from .models import Subscription, User
from .serializers import (CreateSubscriptionSerializer, SubscriptionSerializer,
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
