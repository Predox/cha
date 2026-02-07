from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_remove_verificationcode"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="message_seen",
            field=models.BooleanField(default=False),
        ),
    ]
