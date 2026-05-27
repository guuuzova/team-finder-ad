import random
from io import BytesIO

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

NAME_MAX_LENGTH = 124
PHONE_MAX_LENGTH = 12
ABOUT_MAX_LENGTH = 256

AVATAR_SIZE_PX = 256
AVATAR_FONT_SIZE = 120
AVATAR_BG_COLORS = (
    "#4A6FA5",
    "#6B8E23",
    "#8B4513",
)
AVATAR_TEXT_COLOR = "#FFFFFF"
DEFAULT_LETTER = "?"
RANDOM_FILENAME_RANGE = 10**8


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("surname", "Admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")
        return self._create_user(email, password, **extra_fields)


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
            self.avatar = self._generate_default_avatar()
        super().save(*args, **kwargs)

    def _generate_default_avatar(self):
        bg_color = random.choice(AVATAR_BG_COLORS)
        image = Image.new("RGB", (AVATAR_SIZE_PX, AVATAR_SIZE_PX), bg_color)
        draw = ImageDraw.Draw(image)
        letter = (self.name or DEFAULT_LETTER).strip()[:1].upper() or DEFAULT_LETTER
        try:
            font = ImageFont.truetype("arial.ttf", AVATAR_FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        position = (
            (AVATAR_SIZE_PX - text_w) // 2 - bbox[0],
            (AVATAR_SIZE_PX - text_h) // 2 - bbox[1],
        )
        draw.text(position, letter, fill=AVATAR_TEXT_COLOR, font=font)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        filename = f"{letter.lower()}_{random.randint(0, RANDOM_FILENAME_RANGE)}.png"
        return ContentFile(buffer.getvalue(), name=filename)
