from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_profile_observer_couple_fields"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="is_couple_admin",
            new_name="is_event_admin",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="is_couple",
        ),
        migrations.RemoveField(
            model_name="profile",
            name="partner_name",
        ),
    ]
