import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm

from .models import User

PHONE_RE = re.compile(r"^(\+7|8)\d{10}$")
PHONE_LOCAL_PREFIX = "8"
PHONE_INTERNATIONAL_PREFIX = "+7"
GITHUB_HOSTS = {"github.com", "www.github.com"}


def validate_github_url(value):
    if not value:
        return value
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise forms.ValidationError("Введите корректную ссылку.")
    if parsed.netloc.lower() not in GITHUB_HOSTS:
        raise forms.ValidationError("Ссылка должна вести на github.com.")
    return value


def normalize_phone(value):
    if not value:
        return value
    if value.startswith(PHONE_LOCAL_PREFIX):
        return PHONE_INTERNATIONAL_PREFIX + value[1:]
    return value


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return None
        if not PHONE_RE.match(phone):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
            )
        normalized = normalize_phone(phone)
        qs = User.objects.filter(phone=normalized)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Этот телефон уже используется.")
        return normalized

    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url", ""))


class PasswordChangeForm(DjangoPasswordChangeForm):
    pass
