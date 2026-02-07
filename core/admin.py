from django.contrib import admin
from .models import SiteSettings, Gift, Reservation, Profile


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
    list_display = ("gift", "created_at", "message_hidden_for_admin", "message_seen")
    search_fields = ("gift__title",)
    # Nao exibimos o usuario em list_display para reduzir chance de vazamento em consultas rapidas.
    # Para auditoria tecnica, voce pode abrir o registro individual.


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "is_couple_admin", "is_observer", "is_couple", "partner_name", "created_at")
    list_filter = ("is_couple_admin", "is_observer", "is_couple")
    search_fields = ("phone_number", "user__username", "user__email", "user__first_name", "partner_name")
