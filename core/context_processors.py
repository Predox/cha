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
    if request.user.is_authenticated:
        my_reserved_count = Reservation.objects.filter(user=request.user).count()

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
    }
