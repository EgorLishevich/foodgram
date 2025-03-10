from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=100
    )
    name = models.CharField(
        verbose_name='Название ингридиента',
        max_length=100
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Колличество ингридиентов в рецепте',
        null=True
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('-name',)
        constraints = [
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=['name', 'measurement_unit', 'amount'],
            )
        ]

    def __str__(self):
        return f'{self.measurement_unit}, {self.name}'


class IngredientsInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингридиент',
        related_name='ingredients_in_recipe',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name='Рецепт',
        related_name='recipe_with_ingredients',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Колличество ингридиентов в рецепте',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Ингридиент в врецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'
        ordering = ('recipe__name',)
        constraints = [
            models.UniqueConstraint(
                name='unique_ingridient_in_recipe',
                fields=['recipe', 'ingredient'],
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.ingredient}'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        max_length=40,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=100,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug'],
                name='unique_tags'
            )
        ]

    def __str__(self):
        return self.name


class TagInRecipe(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag,
        verbose_name='теги',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe'
            )
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=100
    )
    text = models.CharField(
        verbose_name='Описание рецепта',
        max_length=500
    )
    created = models.DateTimeField(
        verbose_name='Время и дата создания рецепта',
        auto_now_add=True,
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    image = models.ImageField(
        verbose_name='Фото рецепта',
        blank=True,
        upload_to='recipes/'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты рецепта',
        through='IngredientsInRecipe'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='authored_recipes',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)
        default_related_name = 'recipe'

    def __str__(self):
        return self.name


class UserRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        ordering = ('-user',)
        constraints = [
            models.UniqueConstraint(
                name='unique_user_recipe',
                fields=['recipe', 'user']
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.user}'


class ShoppingCart(UserRecipe):

    class Meta:
        verbose_name = 'Корзина покупок'
        default_related_name = 'shopping_cart'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"
