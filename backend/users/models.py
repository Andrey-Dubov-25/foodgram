from django.contrib.auth.models import AbstractUser
from django.db import models

from core import constants


class MyUser(AbstractUser):
    first_name = models.CharField(
        max_length=constants.FIRST_NAME_LEN,
        blank=True,
        verbose_name='Имя',
        help_text='Имя пользователя'
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_LEN,
        blank=True,
        verbose_name='Фамилия',
        help_text='Фамилия пользователя'
    )
    email = models.EmailField(
        max_length=constants.EMAIL_LEN,
        unique=True,
        verbose_name='Электронная почта',
        help_text='Электронная почта пользователя'
    )
    username = models.CharField(
        max_length=constants.USERNAME_LEN,
        unique=True,
        verbose_name='Ник',
        help_text='Виртуальное имя пользователя'
    )
    avatar = models.ImageField(null=True, blank=True)
    password = models.CharField(
        max_length=256,
        verbose_name='Пароль',
        help_text='Пароль пользователя'
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
