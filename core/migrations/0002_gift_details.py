from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="gift",
            name="image_2",
            field=models.ImageField(blank=True, null=True, upload_to="gifts/"),
        ),
        migrations.AddField(
            model_name="gift",
            name="image_3",
            field=models.ImageField(blank=True, null=True, upload_to="gifts/"),
        ),
        migrations.AddField(
            model_name="gift",
            name="purchase_links",
            field=models.TextField(blank=True),
        ),
    ]
