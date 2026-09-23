# SPDX-License-Identifier: AGPL-3.0-or-later
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_pki", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pkicertificateauthority",
            name="trust_refid",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Fixed trust-store reference id an appliance keys this CA by (OPNsense refid), so a "
                "frontend's client-auth CA list can reference it deterministically. Blank = not in a store.",
                max_length=13,
                validators=[django.core.validators.RegexValidator("^[0-9a-f]{13}$", "13 lowercase hex characters (OPNsense refid).")],
            ),
        ),
        migrations.AddConstraint(
            model_name="pkicertificateauthority",
            constraint=models.UniqueConstraint(
                condition=models.Q(("trust_refid", ""), _negated=True),
                fields=("trust_refid",),
                name="netbox_pki_ca_unique_trust_refid",
            ),
        ),
    ]
