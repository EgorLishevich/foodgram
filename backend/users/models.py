from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

USERNAME_MAX_LENGTH = 160
USER_USERNAME_REGEX = r'(?!me\b)(^[\w.@+-]+\Z)'
FIRST_NAME_MAX_LENGTH = 160
LAST_NAME_MAX_LENGTH = 160
EMAIL_MAX_LENGTH = 160
PASSWORD_MAX_LENGTH = 160


class User(AbstractUser):

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        db_index=True,
        validators=[RegexValidator(regex=USER_USERNAME_REGEX)],
        verbose_name='Юзернейм пользователя',
        unique=True
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя пользователя'
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия пользователя'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта пользователя',
        unique=True
    )
    password = models.CharField(
        max_length=PASSWORD_MAX_LENGTH,
        verbose_name='Пароль пользователя'
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        verbose_name='Аватар пользователя'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username'),

    def __str__(self):
        return self.username


class Subscription(models.Model):

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_subscriber',
        verbose_name='Подписчик',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_author',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('author__username',)
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'], name='unique_subs'
            )
        ]

    def __str__(self):
        return f'{self.author}, {self.subscriber}'
