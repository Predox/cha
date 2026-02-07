from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if not created:
        return
    # Tenta usar username como telefone (o projeto cria usuários com username = telefone).
    phone = instance.username.strip() if isinstance(instance.username, str) else ""
    if not phone:
        phone = None
    Profile.objects.create(user=instance, phone_number=phone)
