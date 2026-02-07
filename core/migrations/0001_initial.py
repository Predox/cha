from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Gift",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="gifts/")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_title", models.CharField(default="Chá de Panela", max_length=80)),
                ("event_date", models.DateField(blank=True, null=True)),
                ("primary_color", models.CharField(default="#0d6efd", max_length=20)),
                ("secondary_color", models.CharField(default="#6c757d", max_length=20)),
                ("background_color", models.CharField(default="#f8f9fa", max_length=20)),
                ("text_color", models.CharField(default="#212529", max_length=20)),
                ("card_color", models.CharField(default="#ffffff", max_length=20)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="VerificationCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_number", models.CharField(blank=True, default="", max_length=20)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("purpose", models.CharField(choices=[("login", "Login"), ("reset_password", "Redefinir senha")], max_length=20)),
                ("channel", models.CharField(choices=[("sms", "SMS"), ("email", "E-mail")], max_length=10)),
                ("code", models.CharField(max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_number", models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ("is_couple_admin", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anonymous_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("gift", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reservation", to="core.gift")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reservations", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
