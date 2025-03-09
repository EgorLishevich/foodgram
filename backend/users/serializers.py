from rest_framework import serializers

from api.serializer import UserProfileSerializer
from recipes.serializer import ShortRecipeSertializer
from users.models import Subscription, User


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
