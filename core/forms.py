from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import get_user_model

from .models import Gift, SiteSettings

User = get_user_model()


class OTPRequestForm(forms.Form):
    phone_number = forms.CharField(
        label="Telefone (com DDD)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex.: (11) 98888-7777"}),
    )
    email = forms.EmailField(
        label="E-mail (opcional)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "seuemail@exemplo.com"}),
    )

    def clean(self):
        cleaned = super().clean()
        phone = (cleaned.get("phone_number") or "").strip()
        email = (cleaned.get("email") or "").strip()
        if not phone and not email:
            raise forms.ValidationError("Informe um telefone ou um e-mail para receber o código.")
        return cleaned


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="Código",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Digite o código recebido"}),
    )


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Telefone (ou usuário)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Telefone (com DDD)"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Sua senha"}),
    )


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
                    "class": "form-control",
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
        label="Título do site",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    event_date = forms.DateField(
        label="Data do evento",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    couple_phone = forms.CharField(
        label="Telefone do casal (login)",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    couple_email = forms.EmailField(
        label="E-mail do casal (recomendado para recuperação)",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    couple_password1 = forms.CharField(
        label="Senha do casal (opcional)",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    couple_password2 = forms.CharField(
        label="Confirmar senha",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("couple_password1") or ""
        p2 = cleaned.get("couple_password2") or ""
        if (p1 or p2) and p1 != p2:
            raise forms.ValidationError("As senhas não conferem.")
        return cleaned


class ResetPasswordForm(forms.Form):
    code = forms.CharField(
        label="Código",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Digite o código recebido"}),
    )
    new_password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1") or ""
        p2 = cleaned.get("new_password2") or ""
        if p1 != p2:
            raise forms.ValidationError("As senhas não conferem.")
        return cleaned
