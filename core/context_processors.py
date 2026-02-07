from datetime import date

from .models import SiteSettings, Gift, Reservation


def site_context(request):
    settings = SiteSettings.get_solo()

    total_gifts = Gift.objects.filter(is_active=True).count()
    reserved_gifts = Reservation.objects.count()
    reserved_percent = round((reserved_gifts / total_gifts) * 100, 1) if total_gifts else 0.0

    days_left = None
    if settings.event_date:
        days_left = (settings.event_date - date.today()).days

    my_reserved_count = 0
    admin_messages = None
    if request.user.is_authenticated:
        my_reserved_count = Reservation.objects.filter(user=request.user).count()

        profile = getattr(request.user, "profile", None)
        is_admin = request.user.is_staff or request.user.is_superuser or (profile and profile.is_event_admin)
        if is_admin:
            base_qs = (
                Reservation.objects.exclude(anonymous_message="")
                .filter(message_hidden_for_admin=False)
                .select_related("gift")
                .order_by("-created_at")
            )
            unseen_qs = base_qs.filter(message_seen=False)
            seen_qs = base_qs.filter(message_seen=True)
            admin_messages = {
                "unseen": list(unseen_qs),
                "seen": list(seen_qs),
                "unseen_count": unseen_qs.count(),
                "seen_count": seen_qs.count(),
            }

    show_welcome_modal = bool(request.session.pop("show_welcome_modal", False))

    return {
        "site_settings": settings,
        "global_stats": {
            "total_gifts": total_gifts,
            "reserved_gifts": reserved_gifts,
            "available_gifts": (total_gifts - reserved_gifts),
            "reserved_percent": reserved_percent,
            "days_left": days_left,
        },
        "my_reserved_count": my_reserved_count,
        "show_welcome_modal": show_welcome_modal,
        "admin_messages": admin_messages,
    }
