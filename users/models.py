from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager
from .utils import generate_default_avatar

NAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
ABOUT_MAX_LENGTH = 256


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    surname = models.CharField(max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH, unique=True, null=True, blank=True
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    favorites = models.ManyToManyField(
        "projects.Project", related_name="interested_users", blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = generate_default_avatar(self.name)
        super().save(*args, **kwargs)
