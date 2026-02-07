from django.conf import settings
from django.db import models


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
    # Um presente pode ter no maximo UMA reserva ativa. Ao cancelar, a reserva e removida.
    gift = models.OneToOneField(Gift, on_delete=models.CASCADE, related_name="reservation")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")

    # Mensagem deve ser anonima (nao armazenamos nome na mensagem)
    anonymous_message = models.TextField(blank=True)
    message_seen = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Reserva: {self.gift_id}"
