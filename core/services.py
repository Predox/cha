import random
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import VerificationCode


def normalize_phone(phone_raw: str) -> str:
    """Normaliza telefone para formato E.164 (default BR se não houver código do país)."""
    digits = re.sub(r"\D+", "", phone_raw or "")
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) >= 12:
        return f"+{digits}"
    if len(digits) in (10, 11):
        return f"+55{digits}"
    return f"+{digits}"


def generate_code(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def twilio_configured() -> bool:
    has_sender = bool(settings.TWILIO_FROM_NUMBER or settings.TWILIO_MESSAGING_SERVICE_SID)
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and has_sender)


def send_code_via_sms(phone_e164: str, code: str) -> None:
    # Import local para não exigir Twilio em ambiente sem SMS
    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    payload = {
        "body": f"Seu código de acesso é: {code}",
        "to": phone_e164,
    }
    if settings.TWILIO_MESSAGING_SERVICE_SID:
        payload["messaging_service_sid"] = settings.TWILIO_MESSAGING_SERVICE_SID
    else:
        payload["from_"] = settings.TWILIO_FROM_NUMBER

    client.messages.create(**payload)


def send_code_via_email(email: str, code: str) -> None:
    subject = "Seu código de acesso"
    message = (
        f"Seu código de acesso é: {code}\n\n"
        "Se você não solicitou, ignore este e-mail."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)


def create_and_send_verification_code(*, phone_number: str, email: str, purpose: str) -> VerificationCode:
    """Cria um OTP e envia por SMS (se configurado) ou por e-mail (fallback)."""
    phone_raw = (phone_number or "").strip()
    email = (email or "").strip()

    code = generate_code(6)
    expires_at = timezone.now() + timedelta(minutes=settings.OTP_TTL_MINUTES)

    channel = None
    phone_e164 = ""

    if phone_raw and twilio_configured():
        phone_e164 = normalize_phone(phone_raw)
        channel = VerificationCode.CHANNEL_SMS
    else:
        channel = VerificationCode.CHANNEL_EMAIL

    verification = VerificationCode.objects.create(
        phone_number=phone_raw,
        email=email,
        purpose=purpose,
        channel=channel,
        code=code,
        expires_at=expires_at,
    )

    if channel == VerificationCode.CHANNEL_SMS and phone_e164:
        send_code_via_sms(phone_e164, code)
    else:
        # Se DEBUG e sem SMTP, o Django pode usar backend de console e imprimir no terminal.
        if email:
            send_code_via_email(email, code)

    return verification
