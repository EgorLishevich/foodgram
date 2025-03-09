from api.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from users.models import User


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
