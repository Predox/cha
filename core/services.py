import re


def normalize_phone(phone_raw: str) -> str:
    """Normaliza telefone para formato E.164 (default BR se nao houver codigo do pais)."""
    digits = re.sub(r"\D+", "", phone_raw or "")
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) >= 12:
        return f"+{digits}"
    if len(digits) in (10, 11):
        return f"+55{digits}"
    return f"+{digits}"
