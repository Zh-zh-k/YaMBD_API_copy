from django.db import models

from users.models import User
from .validators import year_validation

CHOICES = [(i, i) for i in range(1, 11)]


class Categories(models.Model):
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Индификатор', unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genres(models.Model):
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Индификатор', unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=256, db_index=True,
                            verbose_name='Название произведения',
                            help_text='Укажите название произведения')
    year = models.PositiveSmallIntegerField(verbose_name='Год выпуска',
                                            validators=[year_validation],
                                            help_text='Задайте год выпуска')
    description = models.TextField(null=True, blank=True,
                                   verbose_name='Описание')
    category = models.ForeignKey(Categories, verbose_name='Категория',
                                 on_delete=models.SET_NULL,
                                 related_name='titles', blank=True, null=True)
    genre = models.ManyToManyField(Genres, verbose_name='Жанр',
                                   related_name='titles', blank=True)

    class Meta:
        ordering = ('-year',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class GenreToTitle(models.Model):
    """Модель связывающая произведение с жанром"""
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genres, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title} {self.genre}'


class Review(models.Model):

    author = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    title = models.ForeignKey(
        Title, verbose_name='Произведение',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField(verbose_name='Текст отзыва')
    pub_date = models.DateTimeField(
        verbose_name='Дата добавления', auto_now_add=True, db_index=True
    )
    score = models.PositiveSmallIntegerField(choices=CHOICES)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['pub_date']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]


class Comment(models.Model):
    author = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    review = models.ForeignKey(
        Review, verbose_name='Отзыв',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(verbose_name='Текст комментария')
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
