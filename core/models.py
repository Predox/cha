from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_couple_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.phone_number}"


class SiteSettings(models.Model):
    # Singleton
    site_title = models.CharField(max_length=80, default="Chá de Panela")
    event_date = models.DateField(null=True, blank=True)

    primary_color = models.CharField(max_length=20, default="#0d6efd")   # bootstrap primary
    secondary_color = models.CharField(max_length=20, default="#6c757d") # bootstrap secondary
    background_color = models.CharField(max_length=20, default="#f8f9fa")
    text_color = models.CharField(max_length=20, default="#212529")
    card_color = models.CharField(max_length=20, default="#ffffff")

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls) -> "SiteSettings":
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return "Configurações do Site"


class Gift(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="gifts/", blank=True, null=True)
    image_2 = models.ImageField(upload_to="gifts/", blank=True, null=True)
    image_3 = models.ImageField(upload_to="gifts/", blank=True, null=True)
    purchase_links = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_reserved(self) -> bool:
        return hasattr(self, "reservation")

    @property
    def purchase_links_list(self):
        items = []
        for raw in (self.purchase_links or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            if "|" in line:
                label, url = [part.strip() for part in line.split("|", 1)]
            else:
                label, url = "", line
            if not url:
                continue
            if url and not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            if not label:
                label = url
            items.append({"label": label, "url": url})
        return items

    @property
    def images_list(self):
        images = []
        for field in ("image", "image_2", "image_3"):
            file_obj = getattr(self, field)
            if file_obj:
                images.append(
                    {
                        "url": file_obj.url,
                        "alt": f"Imagem do presente {self.title}",
                    }
                )
        return images

    def __str__(self) -> str:
        return self.title


class Reservation(models.Model):
    # Um presente pode ter no máximo UMA reserva ativa. Ao cancelar, a reserva é removida.
    gift = models.OneToOneField(Gift, on_delete=models.CASCADE, related_name="reservation")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")

    # Mensagem deve ser anônima (não armazenamos nome na mensagem)
    anonymous_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Reserva: {self.gift_id}"


class VerificationCode(models.Model):
    PURPOSE_LOGIN = "login"
    PURPOSE_RESET_PASSWORD = "reset_password"
    PURPOSE_CHOICES = [
        (PURPOSE_LOGIN, "Login"),
        (PURPOSE_RESET_PASSWORD, "Redefinir senha"),
    ]

    CHANNEL_SMS = "sms"
    CHANNEL_EMAIL = "email"
    CHANNEL_CHOICES = [
        (CHANNEL_SMS, "SMS"),
        (CHANNEL_EMAIL, "E-mail"),
    ]

    phone_number = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)

    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def is_used(self) -> bool:
        return self.used_at is not None

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
