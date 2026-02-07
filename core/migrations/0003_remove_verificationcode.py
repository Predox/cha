from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_gift_details"),
    ]

    operations = [
        migrations.DeleteModel(
            name="VerificationCode",
        ),
    ]
