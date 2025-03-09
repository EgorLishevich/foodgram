from api.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer
from recipes.serializer import ShortRecipeSertializer
from rest_framework import serializers

from .models import Subscription, User


class UserProfileSerializer(UserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, data):
        user = self.context.get('request').user

        return (
            user.is_authenticated and user.subscription_subscriber.filter(
                author=data.id
            ).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(use_url=True)

    class Meta:
        model = User
        fields = ['avatar']

    def validate(self, attrs):
        avatar = self.initial_data.get('avatar')
        if not avatar:
            raise serializers.ValidationError('Аватар обязателен')

        return attrs


class CreateUserProfileSerializer(UserProfileSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'password', 'id', 'email'
        )
        extra_kwargs = {'password': {'write_only': True}}


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    recipes = serializers.ReadOnlyField(source='author.recipes.all')

    class Meta:
        model = Subscription
        fields = (
            'subscriber', 'recipes', 'author', 'recipes_count'
        )
        extra_kwargs = {
            'author': {'write_only': True},
            'subscriber': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['subscriber'] == attrs['author']:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )

        return attrs

    def to_representation(self, instance):
        pk = UserProfileSerializer(
            instance.author, context={'request': self.context['request']}
        ).data
        pk.update(super().to_representation(instance))
        return pk


class SubscriptionSerializer(UserProfileSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'avatar', 'is_subscribed', 'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return obj.authored_recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.authored_recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return ShortRecipeSertializer(
            recipes, many=True, context={'request': request}
        ).data
