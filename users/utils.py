import random
import re
from io import BytesIO
from urllib.parse import urlparse

from django import forms
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from PIL import Image, ImageDraw, ImageFont

PHONE_RE = re.compile(r"^(\+7|8)\d{10}$")
PHONE_LOCAL_PREFIX = "8"
PHONE_INTERNATIONAL_PREFIX = "+7"
GITHUB_HOSTS = {"github.com", "www.github.com"}

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


def generate_default_avatar(name):
    bg_color = random.choice(AVATAR_BG_COLORS)
    image = Image.new("RGB", (AVATAR_SIZE_PX, AVATAR_SIZE_PX), bg_color)
    draw = ImageDraw.Draw(image)
    letter = (name or DEFAULT_LETTER).strip()[:1].upper() or DEFAULT_LETTER
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


def paginate(request, queryset, page_size):
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(request.GET.get("page"))
