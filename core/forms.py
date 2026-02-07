from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm

from .models import Gift, SiteSettings, Profile
from .services import normalize_phone

User = get_user_model()


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label="Nome, email ou telefone",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome, email ou telefone"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Sua senha"}),
    )

    error_messages = {
        "invalid_login": "Email, telefone, nome ou senha invalidos.",
        "inactive": "Esta conta esta inativa.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        identifier = (cleaned.get("identifier") or "").strip()
        password = cleaned.get("password") or ""
        if not identifier or not password:
            return cleaned

        user = self._find_user(identifier)
        if user:
            self.user_cache = authenticate(self.request, username=user.username, password=password)

        if self.user_cache is None:
            raise forms.ValidationError(self.error_messages["invalid_login"])
        if not self.user_cache.is_active:
            raise forms.ValidationError(self.error_messages["inactive"])

        return cleaned

    def get_user(self):
        return self.user_cache

    def _find_user(self, identifier: str):
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user
        else:
            phone_norm = normalize_phone(identifier)
            if phone_norm:
                profile = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
                if profile:
                    return profile.user
        user = User.objects.filter(username__iexact=identifier).first()
        if user:
            return user
        qs = User.objects.filter(first_name__iexact=identifier)
        if qs.count() == 1:
            return qs.first()
        return None


class RegistrationForm(forms.Form):
    full_name = forms.CharField(
        label="Nome completo",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome completo"}),
    )
    phone_number = forms.CharField(
        label="Telefone",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex.: (11) 98888-7777"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "seuemail@exemplo.com"}),
    )
    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_phone_number(self):
        phone_raw = (self.cleaned_data.get("phone_number") or "").strip()
        phone_norm = normalize_phone(phone_raw)
        if not phone_norm:
            raise forms.ValidationError("Informe um telefone valido.")
        return phone_norm

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        phone = cleaned.get("phone_number") or ""
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("As senhas nao conferem.")

        existing_user = None
        if email:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and existing_user.has_usable_password():
                raise forms.ValidationError("Ja existe uma conta com este email.")

        if phone:
            profile = Profile.objects.filter(phone_number=phone).select_related("user").first()
            if profile:
                phone_user = profile.user
                if existing_user and existing_user != phone_user:
                    raise forms.ValidationError("Email e telefone pertencem a contas diferentes.")
                if phone_user.has_usable_password():
                    raise forms.ValidationError("Este telefone ja esta associado a outra conta.")
                existing_user = phone_user
            else:
                if existing_user and Profile.objects.filter(phone_number=phone).exclude(user=existing_user).exists():
                    raise forms.ValidationError("Este telefone ja esta associado a outra conta.")

        self.existing_user = existing_user
        cleaned["email"] = email
        return cleaned


class DefinePasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class GiftForm(forms.ModelForm):
    class Meta:
        model = Gift
        fields = ["title", "description", "image", "image_2", "image_3", "purchase_links", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "image_2": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "image_3": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "purchase_links": forms.Textarea(
                attrs={
                    "class": "form-control d-none",
                    "rows": 3,
                    "placeholder": "Ex.: Amazon | https://amazon.com/item\nMagazine Luiza | https://...\nOu apenas a URL",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "site_title",
            "event_date",
        ]
        widgets = {
            "site_title": forms.TextInput(attrs={"class": "form-control"}),
            "event_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class SetupForm(forms.Form):
    site_title = forms.CharField(
        label="Titulo do site",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    event_date = forms.DateField(
        label="Data do evento",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    admin_phone = forms.CharField(
        label="Telefone do administrador (login)",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    admin_email = forms.EmailField(
        label="Email do administrador (recomendado para recuperacao)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    admin_password1 = forms.CharField(
        label="Senha do administrador (opcional)",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    admin_password2 = forms.CharField(
        label="Confirmar senha",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("admin_password1") or ""
        p2 = cleaned.get("admin_password2") or ""
        if (p1 or p2) and p1 != p2:
            raise forms.ValidationError("As senhas nao conferem.")
        return cleaned
