from django.contrib import admin
from .models import SiteSettings, Gift, Reservation, VerificationCode, Profile


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_title", "event_date", "updated_at")


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at", "updated_at")
    search_fields = ("title",)
    list_filter = ("is_active",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("gift", "created_at")
    search_fields = ("gift__title",)
    # Não exibimos o usuário em list_display para reduzir chance de vazamento em consultas rápidas.
    # Para auditoria técnica, você pode abrir o registro individual.


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("purpose", "channel", "phone_number", "email", "created_at", "expires_at", "used_at", "attempts")
    list_filter = ("purpose", "channel")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "is_couple_admin", "created_at")
    list_filter = ("is_couple_admin",)
    search_fields = ("phone_number", "user__username", "user__email")
