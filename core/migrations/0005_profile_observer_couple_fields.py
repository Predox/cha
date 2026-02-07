from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_reservation_message_seen"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="is_observer",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="is_couple",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="partner_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="reservation",
            name="message_hidden_for_admin",
            field=models.BooleanField(default=False),
        ),
    ]
