# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored initial migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_pki --check --dry-run   (on a dev/ephemeral NetBox)
# Re-confirm against the pinned NetBox 4.6: the PkiCertificate.service_instance FK target
# (netbox_services.serviceinstance) and the ArrayField(sans) surface.
# Models are Pki-prefixed to avoid a tags reverse-accessor clash with netbox_ssl (E304); the
# netbox_pki_-prefixed constraint names are preserved.
import django.contrib.postgres.fields
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models

_BASE = [
    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
    ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
    ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
    ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
]
_TAGS = ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"))


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("dcim", "0001_initial"),
        ("extras", "0001_initial"),
        # PkiCertificate.service_instance FKs netbox_services.ServiceInstance — its table must exist.
        ("netbox_services", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="PkiCertificateAuthority",
            fields=[
                *_BASE,
                ("name", models.CharField(max_length=100, unique=True)),
                ("ca_type", models.CharField(max_length=16)),
                ("acme_directory_url", models.URLField(blank=True)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("ca_cert_ref", models.CharField(blank=True, max_length=255)),
                _TAGS,
            ],
            options={
                "verbose_name": "Certificate Authority",
                "verbose_name_plural": "Certificate Authorities",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ACMEAccount",
            fields=[
                *_BASE,
                ("contact_email", models.EmailField(max_length=254)),
                ("account_key_ref", models.CharField(max_length=255)),
                ("eab_kid", models.CharField(blank=True, max_length=255)),
                ("eab_hmac_ref", models.CharField(blank=True, max_length=255)),
                ("directory_url", models.URLField(blank=True)),
                ("ca", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="acme_accounts", to="netbox_pki.pkicertificateauthority")),
                _TAGS,
            ],
            options={
                "verbose_name": "ACME Account",
                "ordering": ["ca", "contact_email"],
                "constraints": [models.UniqueConstraint(fields=("ca", "contact_email"), name="netbox_pki_acmeaccount_unique_ca_contact_email")],
            },
        ),
        migrations.CreateModel(
            name="PkiCertificate",
            fields=[
                *_BASE,
                ("common_name", models.CharField(max_length=255)),
                ("sans", django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, default=list, size=None)),
                ("key_algorithm", models.CharField(default="ecdsa_p256", max_length=16)),
                ("challenge_type", models.CharField(default="http01", max_length=16)),
                ("status", models.CharField(default="pending", max_length=16)),
                ("not_before", models.DateTimeField(blank=True, null=True)),
                ("not_after", models.DateTimeField(blank=True, null=True)),
                ("auto_renew", models.BooleanField(default=True)),
                ("renew_before_days", models.PositiveIntegerField(default=30)),
                ("key_ref", models.CharField(max_length=255)),
                ("cert_ref", models.CharField(blank=True, max_length=255)),
                ("ca", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="certificates", to="netbox_pki.pkicertificateauthority")),
                ("acme_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="certificates", to="netbox_pki.acmeaccount")),
                ("service_instance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="certificates", to="netbox_services.serviceinstance")),
                _TAGS,
            ],
            options={
                "verbose_name": "Certificate",
                "ordering": ["common_name", "ca"],
                "constraints": [models.UniqueConstraint(fields=("common_name", "ca"), name="netbox_pki_certificate_unique_common_name_ca")],
            },
        ),
    ]
