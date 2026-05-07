from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0003_billing_profile_user_not_unique"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="billingprofile",
            constraint=models.UniqueConstraint(
                fields=("organization_id",),
                name="uq_billing_profile_org",
                condition=models.Q(organization_id__gt=""),
            ),
        ),
    ]
