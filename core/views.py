from datetime import date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Exists, OuterRef, Value, BooleanField
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .decorators import couple_admin_required
from .forms import (
    OTPRequestForm,
    OTPVerifyForm,
    PhoneAuthenticationForm,
    DefinePasswordForm,
    ResetPasswordForm,
    GiftForm,
    SiteSettingsForm,
    SetupForm,
)
from .models import Gift, Reservation, SiteSettings, VerificationCode, Profile
from .services import create_and_send_verification_code, normalize_phone, twilio_configured


User = get_user_model()


def home(request):
    return redirect("catalogo")


def setup(request, token: str):
    """Setup inicial protegido por token em variável de ambiente.

    URL: /setup/<SETUP_TOKEN>/
    Funciona apenas se ainda não existir um casal administrador.
    """
    if not settings.SETUP_TOKEN or token != settings.SETUP_TOKEN:
        raise Http404()

    if Profile.objects.filter(is_couple_admin=True).exists():
        messages.info(request, "O setup inicial já foi concluído.")
        return redirect("login_codigo")

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

        phone_raw = form.cleaned_data["couple_phone"]
        phone_norm = normalize_phone(phone_raw)
        email = (form.cleaned_data.get("couple_email") or "").strip()

        username = phone_norm or phone_raw.strip()
        # Cria usuário do casal
        if User.objects.filter(username=username).exists():
            messages.error(request, "Já existe um usuário com este telefone. Faça login e peça para marcar como casal no banco.")
            return redirect("login_codigo")

        user = User.objects.create(username=username, email=email)
        p1 = (form.cleaned_data.get("couple_password1") or "").strip()
        if p1:
            user.set_password(p1)
        else:
            user.set_unusable_password()
        user.save()

        # Marca perfil como casal
        profile = user.profile
        profile.phone_number = phone_norm or phone_raw.strip()
        profile.is_couple_admin = True
        profile.save()

        messages.success(request, "Setup concluído. Agora faça login.")
        return redirect("login_codigo")

    return render(request, "setup.html", {"form": form})


def login_codigo(request):
    """Login principal por código (SMS se configurado / e-mail como fallback)."""
    if request.user.is_authenticated:
        return redirect("catalogo")

    form = OTPRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        phone = (form.cleaned_data.get("phone_number") or "").strip()
        email = (form.cleaned_data.get("email") or "").strip()

        # Regras de envio:
        # - Se SMS configurado e telefone informado => SMS
        # - Caso contrário => exige e-mail
        if not (twilio_configured() and phone) and not email:
            messages.error(
                request,
                "Para enviar o código por e-mail, informe um e-mail. "
                "Ou configure SMS (Twilio) e informe um telefone.",
            )
            return render(request, "auth/login_codigo.html", {"form": form})

        verification = create_and_send_verification_code(
            phone_number=phone,
            email=email,
            purpose=VerificationCode.PURPOSE_LOGIN,
        )
        request.session["verification_id"] = verification.id
        request.session["verification_purpose"] = VerificationCode.PURPOSE_LOGIN

        if verification.channel == VerificationCode.CHANNEL_SMS:
            messages.success(request, "Código enviado por SMS.")
        else:
            messages.success(request, "Código enviado por e-mail.")
        return redirect("verificar_codigo")

    return render(request, "auth/login_codigo.html", {"form": form})


def verificar_codigo(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    verification_id = request.session.get("verification_id")
    purpose = request.session.get("verification_purpose")
    if not verification_id or purpose != VerificationCode.PURPOSE_LOGIN:
        return redirect("login_codigo")

    verification = get_object_or_404(VerificationCode, id=verification_id)

    if verification.is_used() or verification.is_expired():
        messages.error(request, "Este código expirou. Solicite um novo.")
        request.session.pop("verification_id", None)
        request.session.pop("verification_purpose", None)
        return redirect("login_codigo")

    form = OTPVerifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = (form.cleaned_data["code"] or "").strip()

        verification.attempts += 1
        verification.save(update_fields=["attempts"])

        if code != verification.code:
            messages.error(request, "Código inválido.")
            return render(request, "auth/verificar_codigo.html", {"form": form})

        # OK
        verification.mark_used()
        request.session.pop("verification_id", None)
        request.session.pop("verification_purpose", None)

        phone_norm = normalize_phone(verification.phone_number) if verification.phone_number else ""
        email = (verification.email or "").strip()

        user = None

        if phone_norm:
            profile = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
            if profile:
                user = profile.user

        if not user and email:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            # cria usuário
            username = phone_norm or email
            # garante unicidade
            if User.objects.filter(username=username).exists():
                username = f"{username}-{User.objects.count()+1}"
            user = User.objects.create(username=username, email=email)
            user.set_unusable_password()
            user.save()

        # garante dados no perfil
        if hasattr(user, "profile"):
            if phone_norm and user.profile.phone_number != phone_norm:
                # se já existe outro usuário com este phone, bloqueia
                if Profile.objects.filter(phone_number=phone_norm).exclude(user=user).exists():
                    messages.error(request, "Este telefone já está associado a outra conta.")
                    return redirect("login_codigo")
                user.profile.phone_number = phone_norm
                user.profile.save(update_fields=["phone_number"])
        else:
            # Muito improvável, mas…
            Profile.objects.create(user=user, phone_number=phone_norm or None)

        login(request, user)
        request.session["show_welcome_modal"] = True
        messages.success(request, "Login realizado com sucesso.")
        return redirect("catalogo")

    return render(request, "auth/verificar_codigo.html", {"form": form})


def login_senha(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    form = PhoneAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        request.session["show_welcome_modal"] = True
        return redirect("catalogo")

    return render(request, "auth/login_senha.html", {"form": form})


@login_required
def sair(request):
    logout(request)
    return redirect("login_codigo")


def esqueci_senha(request):
    """Inicia fluxo de redefinição de senha via código (SMS/email)."""
    if request.user.is_authenticated:
        return redirect("catalogo")

    form = OTPRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        phone = (form.cleaned_data.get("phone_number") or "").strip()
        email = (form.cleaned_data.get("email") or "").strip()

        user = None
        phone_norm = normalize_phone(phone) if phone else ""

        if phone_norm:
            profile = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
            if profile:
                user = profile.user

        if not user and email:
            user = User.objects.filter(email__iexact=email).first()

        # Segurança: não revela se existe ou não conta
        # Decide melhor contato para envio
        send_email = email
        send_phone = phone
        if user:
            # usa o que houver na conta (prioriza telefone se configurado SMS)
            if twilio_configured() and phone_norm:
                send_phone = phone_norm
            else:
                send_email = user.email or email

        if not (twilio_configured() and phone) and not send_email:
            messages.error(
                request,
                "Para redefinir senha por e-mail, informe um e-mail. "
                "Ou configure SMS (Twilio) e informe um telefone.",
            )
            return render(request, "auth/esqueci_senha.html", {"form": form})

        verification = create_and_send_verification_code(
            phone_number=send_phone,
            email=send_email,
            purpose=VerificationCode.PURPOSE_RESET_PASSWORD,
        )
        request.session["verification_id"] = verification.id
        request.session["verification_purpose"] = VerificationCode.PURPOSE_RESET_PASSWORD
        if user:
            request.session["reset_user_id"] = user.id
        else:
            request.session["reset_user_id"] = None

        messages.success(request, "Se os dados estiverem corretos, você receberá um código para redefinir a senha.")
        return redirect("redefinir_senha")

    return render(request, "auth/esqueci_senha.html", {"form": form})


def redefinir_senha(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    verification_id = request.session.get("verification_id")
    purpose = request.session.get("verification_purpose")
    if not verification_id or purpose != VerificationCode.PURPOSE_RESET_PASSWORD:
        return redirect("esqueci_senha")

    verification = get_object_or_404(VerificationCode, id=verification_id)
    if verification.is_used() or verification.is_expired():
        messages.error(request, "Este código expirou. Solicite um novo.")
        request.session.pop("verification_id", None)
        request.session.pop("verification_purpose", None)
        request.session.pop("reset_user_id", None)
        return redirect("esqueci_senha")

    # Descobre o usuário
    user = None
    reset_user_id = request.session.get("reset_user_id")
    if reset_user_id:
        user = User.objects.filter(id=reset_user_id).first()

    if not user:
        # tenta achar por telefone/email do verification
        phone_norm = normalize_phone(verification.phone_number) if verification.phone_number else ""
        if phone_norm:
            profile = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
            if profile:
                user = profile.user
        if not user and verification.email:
            user = User.objects.filter(email__iexact=verification.email).first()

    if not user:
        messages.error(request, "Não foi possível identificar a conta. Solicite novamente.")
        return redirect("esqueci_senha")

    form = ResetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = (form.cleaned_data["code"] or "").strip()

        verification.attempts += 1
        verification.save(update_fields=["attempts"])

        if code != verification.code:
            messages.error(request, "Código inválido.")
            return render(request, "auth/redefinir_senha.html", {"form": form})

        # Define senha
        user.set_password(form.cleaned_data["new_password1"])
        user.save()

        verification.mark_used()
        request.session.pop("verification_id", None)
        request.session.pop("verification_purpose", None)
        request.session.pop("reset_user_id", None)

        messages.success(request, "Senha redefinida. Faça login.")
        return redirect("login_senha")

    return render(request, "auth/redefinir_senha.html", {"form": form})


@login_required
def definir_senha(request):
    """Opcional: define/atualiza senha para login por senha."""
    form = DefinePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Senha atualizada.")
        return redirect("catalogo")
    return render(request, "auth/definir_senha.html", {"form": form})


@login_required
def catalogo(request):
    qs = Gift.objects.filter(is_active=True).order_by("title")

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
        return HttpResponseForbidden("Método não permitido.")

    gift = get_object_or_404(Gift.objects.select_for_update(), id=gift_id, is_active=True)

    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente já está reservado por outra pessoa.")
        return redirect("catalogo")

    msg = (request.POST.get("anonymous_message") or "").strip()

    # Reforça anonimato: remove assinaturas óbvias? (não garante)
    # Não removemos conteúdo, apenas orientamos no UI. Aqui apenas limitamos tamanho.
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
        return HttpResponseForbidden("Método não permitido.")

    gift = get_object_or_404(Gift, id=gift_id, is_active=True)
    reservation = Reservation.objects.filter(gift=gift, user=request.user).first()
    if not reservation:
        messages.error(request, "Você não possui reserva deste presente.")
        return redirect("catalogo")

    reservation.delete()
    messages.success(request, "Reserva cancelada.")
    return redirect("catalogo")


# ======================
# Painel do casal (anônimo)
# ======================

@couple_admin_required
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


@couple_admin_required
def painel_presentes(request):
    gifts = Gift.objects.all().order_by("-created_at").annotate(
        reserved=Exists(Reservation.objects.filter(gift=OuterRef("pk")))
    )
    return render(request, "painel/presentes_list.html", {"gifts": gifts})


@couple_admin_required
def painel_presente_novo(request):
    form = GiftForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Presente criado.")
        return redirect("painel_presentes")
    return render(request, "painel/presente_form.html", {"form": form, "mode": "new"})


@couple_admin_required
def painel_presente_editar(request, gift_id: int):
    gift = get_object_or_404(Gift, id=gift_id)
    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente já foi reservado e não pode ser editado.")
        return redirect("painel_presentes")

    form = GiftForm(request.POST or None, request.FILES or None, instance=gift)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Presente atualizado.")
        return redirect("painel_presentes")
    return render(request, "painel/presente_form.html", {"form": form, "mode": "edit", "gift": gift})


@couple_admin_required
def painel_presente_excluir(request, gift_id: int):
    gift = get_object_or_404(Gift, id=gift_id)
    if Reservation.objects.filter(gift=gift).exists():
        messages.error(request, "Este presente já foi reservado e não pode ser excluído.")
        return redirect("painel_presentes")

    if request.method == "POST":
        gift.delete()
        messages.success(request, "Presente excluído.")
        return redirect("painel_presentes")

    return render(request, "painel/presente_confirm_delete.html", {"gift": gift})


@couple_admin_required
def painel_personalizacao(request):
    site = SiteSettings.get_solo()
    form = SiteSettingsForm(request.POST or None, instance=site)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Personalização salva. As mudanças já valem para todo o site.")
        return redirect("painel_personalizacao")
    return render(request, "painel/personalizacao.html", {"form": form})


@couple_admin_required
def painel_mensagens(request):
    # Mensagens anônimas (não exibimos usuário)
    reservations = Reservation.objects.exclude(anonymous_message="").select_related("gift").order_by("-created_at")
    return render(request, "painel/mensagens.html", {"reservations": reservations})
