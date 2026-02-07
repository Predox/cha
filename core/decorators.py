from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from functools import wraps


def couple_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = getattr(request.user, "profile", None)
        if not profile or not profile.is_couple_admin:
            return HttpResponseForbidden("Acesso restrito ao painel do casal.")
        return view_func(request, *args, **kwargs)

    return _wrapped
