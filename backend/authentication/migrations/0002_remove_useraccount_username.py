# Generated manually for email-only accounts; JWT resolves users by user_id.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_add_work_item_candidate_table"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="useraccount",
            name="users_usernam_baeb4b_idx",
        ),
        migrations.RemoveField(
            model_name="useraccount",
            name="username",
        ),
    ]
