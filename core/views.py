from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import event_admin_required, observer_required
from .forms import (
    LoginForm,
    RegistrationForm,
    DefinePasswordForm,
    GiftForm,
    SiteSettingsForm,
    SetupForm,
)
from .models import Gift, Reservation, SiteSettings, Profile
from .services import normalize_phone

User = get_user_model()


def home(request):
    return redirect("catalogo")


def _unique_username_from_email(email: str) -> str:
    base = (email or "").strip().lower()
    if not base:
        base = "usuario"
    if not User.objects.filter(username__iexact=base).exists():
        return base
    counter = 2
    while True:
        candidate = f"{base}-{counter}"
        if not User.objects.filter(username__iexact=candidate).exists():
            return candidate
        counter += 1


def setup(request, token: str):
    """Setup inicial protegido por token em variavel de ambiente.

    URL: /setup/<SETUP_TOKEN>/
    Funciona apenas se ainda nao existir um administrador.
    """
    if not settings.SETUP_TOKEN or token != settings.SETUP_TOKEN:
        raise Http404()

    if Profile.objects.filter(is_event_admin=True).exists():
        messages.info(request, "O setup inicial ja foi concluido.")
        return redirect("login")

    form = SetupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # Site settings
        site = SiteSettings.get_solo()
        site.site_title = form.cleaned_data["site_title"]
        site.event_date = form.cleaned_data.get("event_date")

        # Cores (opcionais)
        for field in ["primary_color", "secondary_color", "background_color", "text_color", "card_color"]:
            value = (form.cleaned_data.get(field) or "").strip()
            if value:
                setattr(site, field, value)
        site.save()

        phone_raw = form.cleaned_data["admin_phone"]
        phone_norm = normalize_phone(phone_raw)
        email = (form.cleaned_data.get("admin_email") or "").strip().lower()

        username = phone_norm or phone_raw.strip()
        # Cria usuario administrador
        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Ja existe um usuario com este telefone. Faca login e peca para marcar como admin no banco.",
            )
            return redirect("login")

        user = User.objects.create(username=username, email=email)
        p1 = (form.cleaned_data.get("admin_password1") or "").strip()
        if p1:
            user.set_password(p1)
        else:
            user.set_unusable_password()
        user.save()

        # Marca perfil como admin
        profile = user.profile
        profile.phone_number = phone_norm or phone_raw.strip()
        profile.is_event_admin = True
        profile.save()

        messages.success(request, "Setup concluido. Agora faca login.")
        return redirect("login")

    return render(request, "setup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        request.session["show_welcome_modal"] = True
        messages.success(request, "Login realizado com sucesso.")
        return redirect("catalogo")

    return render(request, "auth/login.html", {"form": form})


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        full_name = (form.cleaned_data.get("full_name") or "").strip()
        email = (form.cleaned_data.get("email") or "").strip().lower()
        phone = form.cleaned_data.get("phone_number") or ""
        password = form.cleaned_data.get("password1") or ""

        existing_user = getattr(form, "existing_user", None)
        if existing_user:
            user = existing_user
            if not user.username:
                user.username = _unique_username_from_email(email)
        else:
            username = _unique_username_from_email(email)
            user = User(username=username, email=email)

        user.email = email
        user.first_name = full_name
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            if existing_user:
                raise
            # Garante unicidade mesmo em casos de colisao de username
            fallback = f"{email}-{User.objects.count() + 1}"
            user.username = _unique_username_from_email(fallback)
            user.save()

        profile = getattr(user, "profile", None)
        if not profile:
            profile = Profile.objects.create(user=user)
        profile.phone_number = phone
        profile.save(update_fields=["phone_number"])

        login(request, user)
        request.session["show_welcome_modal"] = True
        messages.success(request, "Cadastro realizado com sucesso.")
        return redirect("catalogo")

    return render(request, "auth/cadastro.html", {"form": form})


@login_required
def sair(request):
    logout(request)
    return redirect("login")


@login_required
def definir_senha(request):
    """Define/atualiza senha do usuario."""
    form = DefinePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Senha atualizada.")
        return redirect("catalogo")
    return render(request, "auth/definir_senha.html", {"form": form})


@login_required
def catalogo(request):
    qs = Gift.objects.filter(is_active=True).order_by("title").select_related(
        "reservation__user",
        "reservation__user__profile",
    )

    reserved_exists = Reservation.objects.filter(gift=OuterRef("pk"))
    reserved_by_me = Reservation.objects.filter(gift=OuterRef("pk"), user=request.user)

    gifts = qs.annotate(
        reserved=Exists(reserved_exists),
        reserved_by_me=Exists(reserved_by_me),
    )

    return render(request, "catalogo/catalogo.html", {"gifts": gifts})


@login_required
def meus_presentes(request):
    reservations = Reservation.objects.filter(user=request.user).select_related("gift").order_by("-created_at")
    return render(request, "catalogo/meus_presentes.html", {"reservations": reservations})


@login_required
@transaction.atomic
def reservar_presente(request, gift_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")

    gift = get_object_or_404(Gift.objects.select_for_update(), id=gift_id, is_active=True)

    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente ja esta reservado por outra pessoa.")
        return redirect("catalogo")

    msg = (request.POST.get("anonymous_message") or "").strip()

    # Reforca anonimato: remove assinaturas obvias? (nao garante)
    # Nao removemos conteudo, apenas orientamos no UI. Aqui apenas limitamos tamanho.
    if len(msg) > 1000:
        msg = msg[:1000]

    Reservation.objects.create(
        gift=gift,
        user=request.user,
        anonymous_message=msg,
    )

    messages.success(request, "Presente reservado com sucesso.")
    return redirect("catalogo")


@login_required
@transaction.atomic
def cancelar_reserva(request, gift_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")

    gift = get_object_or_404(Gift, id=gift_id, is_active=True)
    reservation = Reservation.objects.filter(gift=gift, user=request.user).first()
    if not reservation:
        messages.error(request, "Voce nao possui reserva deste presente.")
        return redirect("catalogo")

    reservation.delete()
    messages.success(request, "Reserva cancelada.")
    return redirect("catalogo")


# ======================
# Painel administrativo
# ======================

@event_admin_required
def painel_dashboard(request):
    total = Gift.objects.filter(is_active=True).count()
    reserved = Reservation.objects.count()
    available = total - reserved
    percent = round((reserved / total) * 100, 1) if total else 0.0
    # CSS precisa de ponto como separador decimal
    percent_css = f"{percent:.2f}"
    percent_display = f"{percent:.0f}"

    site = SiteSettings.get_solo()
    days_left = None
    if site.event_date:
        days_left = (site.event_date - date.today()).days

    # Lista resumida de presentes
    gifts = Gift.objects.filter(is_active=True).order_by("title").annotate(
        reserved=Exists(Reservation.objects.filter(gift=OuterRef("pk")))
    )

    return render(
        request,
        "painel/dashboard.html",
        {
            "total": total,
            "reserved": reserved,
            "available": available,
            "percent": percent,
            "percent_css": percent_css,
            "percent_display": percent_display,
            "days_left": days_left,
            "gifts": gifts,
        },
    )


@event_admin_required
def painel_presentes(request):
    gifts = Gift.objects.all().order_by("-created_at").annotate(
        reserved=Exists(Reservation.objects.filter(gift=OuterRef("pk")))
    )
    total = gifts.count()
    reserved = Reservation.objects.count()
    available = total - reserved
    return render(
        request,
        "painel/presentes_list.html",
        {"gifts": gifts, "total": total, "reserved": reserved, "available": available},
    )


@event_admin_required
def painel_presente_novo(request):
    form = GiftForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Presente criado.")
        return redirect("painel_presentes")
    return render(request, "painel/presente_form.html", {"form": form, "mode": "new"})


@event_admin_required
def painel_presente_editar(request, gift_id: int):
    gift = get_object_or_404(Gift, id=gift_id)
    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente ja foi reservado e nao pode ser editado.")
        return redirect("painel_presentes")

    form = GiftForm(request.POST or None, request.FILES or None, instance=gift)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Presente atualizado.")
        return redirect("painel_presentes")
    return render(request, "painel/presente_form.html", {"form": form, "mode": "edit", "gift": gift})


@event_admin_required
def painel_presente_excluir(request, gift_id: int):
    gift = get_object_or_404(Gift, id=gift_id)
    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente ja foi reservado e nao pode ser excluido.")
        return redirect("painel_presentes")

    if request.method == "POST":
        gift.delete()
        messages.success(request, "Presente excluido.")
        return redirect("painel_presentes")

    return render(request, "painel/presente_confirm_delete.html", {"gift": gift})


@event_admin_required
def painel_personalizacao(request):
    site = SiteSettings.get_solo()
    form = SiteSettingsForm(request.POST or None, instance=site)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Personalizacao salva. As mudancas ja valem para todo o site.")
        return redirect("painel_personalizacao")
    return render(request, "painel/personalizacao.html", {"form": form})


@event_admin_required
def painel_mensagens(request):
    # Mensagens anonimas (nao exibimos usuario)
    base_qs = (
        Reservation.objects.exclude(anonymous_message="")
        .filter(message_hidden_for_admin=False)
        .select_related("gift")
        .order_by("-created_at")
    )
    unseen = base_qs.filter(message_seen=False)
    seen = base_qs.filter(message_seen=True)
    return render(
        request,
        "painel/mensagens.html",
        {
            "unseen_reservations": unseen,
            "seen_reservations": seen,
            "unseen_count": unseen.count(),
            "seen_count": seen.count(),
        },
    )


@event_admin_required
def marcar_mensagem_vista(request, reservation_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    Reservation.objects.filter(id=reservation_id, message_hidden_for_admin=False).update(message_seen=True)
    return redirect(request.META.get("HTTP_REFERER", "painel_mensagens"))


@event_admin_required
def marcar_todas_mensagens_vistas(request):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    Reservation.objects.exclude(anonymous_message="").filter(
        message_seen=False,
        message_hidden_for_admin=False,
    ).update(message_seen=True)
    return redirect(request.META.get("HTTP_REFERER", "painel_mensagens"))


@observer_required
def observador_mensagens(request):
    reservations = (
        Reservation.objects.exclude(anonymous_message="")
        .select_related("gift", "user", "user__profile")
        .order_by("-created_at")
    )
    users = User.objects.select_related("profile").order_by("first_name", "username")
    reservations_by_user = {}
    for reservation in Reservation.objects.select_related("gift", "user").order_by("gift__title"):
        reservations_by_user.setdefault(reservation.user_id, []).append(reservation)

    observer_users = []
    for user in users:
        profile = getattr(user, "profile", None)
        display_name = profile.display_name if profile else (user.get_full_name() or user.username)
        user_reservations = reservations_by_user.get(user.id, [])
        observer_users.append(
            {
                "id": user.id,
                "name": display_name,
                "email": user.email,
                "reservations": user_reservations,
                "gifts": [res.gift.title for res in user_reservations],
            }
        )

    return render(
        request,
        "observador/mensagens.html",
        {"reservations": reservations, "observer_users": observer_users},
    )


@observer_required
def observador_ocultar_mensagem(request, reservation_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    Reservation.objects.filter(id=reservation_id).update(message_hidden_for_admin=True)
    return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))


@observer_required
def observador_mostrar_mensagem(request, reservation_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    Reservation.objects.filter(id=reservation_id).update(message_hidden_for_admin=False)
    return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))


@observer_required
def observador_excluir_mensagem(request, reservation_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    Reservation.objects.filter(id=reservation_id).update(
        anonymous_message="",
        message_hidden_for_admin=True,
        message_seen=True,
    )
    return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))


@observer_required
def observador_alterar_senha(request, user_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    password1 = (request.POST.get("password1") or "").strip()
    password2 = (request.POST.get("password2") or "").strip()
    if not password1 or not password2:
        messages.error(request, "Informe a nova senha e a confirmacao.")
        return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))
    if password1 != password2:
        messages.error(request, "As senhas nao conferem.")
        return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))

    user = get_object_or_404(User, id=user_id)
    user.set_password(password1)
    user.save(update_fields=["password"])
    messages.success(request, "Senha atualizada com sucesso.")
    return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))


@observer_required
def observador_remover_reservas(request, user_id: int):
    if request.method != "POST":
        return HttpResponseForbidden("Metodo nao permitido.")
    reservation_ids = request.POST.getlist("reservation_ids")
    if not reservation_ids:
        messages.info(request, "Nenhuma reserva selecionada.")
        return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))
    Reservation.objects.filter(user_id=user_id, id__in=reservation_ids).delete()
    messages.success(request, "Reservas removidas.")
    return redirect(request.META.get("HTTP_REFERER", "observador_mensagens"))
