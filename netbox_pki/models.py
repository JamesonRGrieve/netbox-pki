# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native PKI source-of-truth models. ``PkiCertificateAuthority`` is the trust anchor (an ACME
directory, an internal/external CA, or a self-signed root); ``ACMEAccount`` registers against an
ACME CA; ``PkiCertificate`` is an issued leaf certificate — its subject, SANs, key algorithm,
validity window, renewal policy, and status — optionally linked to the
``netbox_services.ServiceInstance`` that terminates TLS with it.

The models are ``Pki``-prefixed (with clean ``verbose_name`` UI labels) so their inherited ``tags``
reverse accessors do not collide with the pre-installed ``netbox_ssl`` plugin's own
``Certificate`` / ``CertificateAuthority`` models (Django system check E304).

FKs to sibling models use STRING labels ("netbox_services.ServiceInstance") — never import those
into this module.

SECRET POLICY: private key material and ACME account keys are NEVER fields here. The ``*_ref``
CharFields (``ca_cert_ref``, ``account_key_ref``, ``eab_hmac_ref``, ``key_ref``, ``cert_ref``) are
OpenBao path references (the netbox-services convention); the key/secret value stays in OpenBao.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from netbox.models import NetBoxModel

from .choices import CATypeChoices, CertStatusChoices, ChallengeTypeChoices, KeyAlgorithmChoices


class PkiCertificateAuthority(NetBoxModel):
    """A certificate authority the estate trusts or issues from. For ``ca_type=acme`` the
    ``acme_directory_url`` names the directory endpoint (Let's Encrypt / ZeroSSL / an internal
    step-ca). ``ca_cert_ref`` is an OpenBao path to the CA chain — never the key material."""

    name = models.CharField(max_length=100, unique=True)
    ca_type = models.CharField(max_length=16, choices=CATypeChoices)
    acme_directory_url = models.URLField(
        blank=True, help_text="ACME directory endpoint (ca_type=acme) — LE/ZeroSSL/step-ca."
    )
    contact_email = models.EmailField(blank=True)
    ca_cert_ref = models.CharField(
        max_length=255, blank=True, help_text="OpenBao path to the CA chain — NEVER the key."
    )
    trust_refid = models.CharField(
        max_length=13,
        blank=True,
        default="",
        validators=[RegexValidator(r"^[0-9a-f]{13}$", "13 lowercase hex characters (OPNsense refid).")],
        help_text="Fixed trust-store reference id an appliance keys this CA by (OPNsense refid), so a "
        "frontend's client-auth CA list can reference it deterministically. Blank = not in a store.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Certificate Authority"
        verbose_name_plural = "Certificate Authorities"
        constraints = [
            models.UniqueConstraint(
                fields=["trust_refid"], condition=~models.Q(trust_refid=""), name="netbox_pki_ca_unique_trust_refid"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.ca_type})"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pki:pkicertificateauthority", args=[self.pk])

    def get_ca_type_color(self):
        return CATypeChoices.colors.get(self.ca_type)


class ACMEAccount(NetBoxModel):
    """A registered ACME account against an ACME :class:`PkiCertificateAuthority`.
    ``account_key_ref`` is an OpenBao path to the account key (never the key value). ``eab_kid`` /
    ``eab_hmac_ref`` carry External Account Binding for CAs that require it (e.g. ZeroSSL, an
    internal step-ca)."""

    ca = models.ForeignKey(
        PkiCertificateAuthority, on_delete=models.CASCADE, related_name="acme_accounts"
    )
    contact_email = models.EmailField()
    account_key_ref = models.CharField(
        max_length=255, help_text="OpenBao path to the ACME account key — NEVER the key."
    )
    eab_kid = models.CharField(
        max_length=255, blank=True, help_text="External Account Binding key id (if the CA requires)."
    )
    eab_hmac_ref = models.CharField(
        max_length=255, blank=True, help_text="OpenBao path to the EAB HMAC key — NEVER the secret."
    )
    directory_url = models.URLField(
        blank=True, help_text="Directory endpoint override (blank = the CA's acme_directory_url)."
    )

    class Meta:
        ordering = ["ca", "contact_email"]
        verbose_name = "ACME Account"
        constraints = [
            models.UniqueConstraint(
                fields=["ca", "contact_email"],
                name="netbox_pki_acmeaccount_unique_ca_contact_email",
            ),
        ]

    def __str__(self):
        return f"{self.contact_email} @ {self.ca.name}"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pki:acmeaccount", args=[self.pk])


class PkiCertificate(NetBoxModel):
    """An issued leaf certificate. ``common_name`` + ``sans`` are the subject and subject-alt names;
    ``ca`` is the issuing authority (PROTECT — a CA with live certificates cannot be deleted out from
    under them); ``acme_account`` is the account used when the CA is ACME. ``key_algorithm`` /
    ``challenge_type`` drive issuance; ``status`` + ``not_before`` / ``not_after`` + ``auto_renew`` /
    ``renew_before_days`` drive the renewal loop. ``key_ref`` / ``cert_ref`` are OpenBao paths to the
    private key and the issued cert/fullchain — never the material itself."""

    common_name = models.CharField(max_length=255)
    sans = ArrayField(
        models.CharField(max_length=255), default=list, blank=True,
        help_text="Subject alternative names.",
    )
    ca = models.ForeignKey(
        PkiCertificateAuthority, on_delete=models.PROTECT, related_name="certificates"
    )
    acme_account = models.ForeignKey(
        ACMEAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="certificates"
    )
    key_algorithm = models.CharField(
        max_length=16, choices=KeyAlgorithmChoices, default=KeyAlgorithmChoices.ECDSA_P256
    )
    challenge_type = models.CharField(
        max_length=16, choices=ChallengeTypeChoices, default=ChallengeTypeChoices.HTTP01
    )
    status = models.CharField(
        max_length=16, choices=CertStatusChoices, default=CertStatusChoices.PENDING
    )
    not_before = models.DateTimeField(null=True, blank=True)
    not_after = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    renew_before_days = models.PositiveIntegerField(
        default=30, help_text="Renew this many days before not_after."
    )
    key_ref = models.CharField(
        max_length=255, help_text="OpenBao path to the private key — NEVER the key."
    )
    cert_ref = models.CharField(
        max_length=255, blank=True, help_text="OpenBao path to the issued cert/fullchain."
    )
    service_instance = models.ForeignKey(
        "netbox_services.ServiceInstance", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="certificates",
        help_text="The netbox-services instance that terminates TLS with this cert (composition link).",
    )

    class Meta:
        ordering = ["common_name", "ca"]
        verbose_name = "Certificate"
        constraints = [
            models.UniqueConstraint(
                fields=["common_name", "ca"],
                name="netbox_pki_certificate_unique_common_name_ca",
            ),
        ]

    def __str__(self):
        return f"{self.common_name} [{self.ca.name}]"

    def get_absolute_url(self):
        return reverse("plugins:netbox_pki:pkicertificate", args=[self.pk])

    def get_status_color(self):
        return CertStatusChoices.colors.get(self.status)

    def get_key_algorithm_color(self):
        return KeyAlgorithmChoices.colors.get(self.key_algorithm)

    def get_challenge_type_color(self):
        return ChallengeTypeChoices.colors.get(self.challenge_type)

    @property
    def is_expiring(self):
        """Computed (not stored): True when the cert is inside its renewal window — either flagged
        ``expiring`` outright, or ``not_after`` is within ``renew_before_days`` of now. Returns
        False when ``not_after`` is unknown (a pending cert has no validity window yet)."""
        if self.status == CertStatusChoices.EXPIRING:
            return True
        if self.not_after is None:
            return False
        return timezone.now() >= self.not_after - timedelta(days=self.renew_before_days)

    def clean(self):
        super().clean()
        if self.acme_account_id and self.acme_account.ca_id != self.ca_id:
            raise ValidationError("The ACME account must belong to the issuing CA.")
        if self.ca_id and self.ca.ca_type == CATypeChoices.ACME and not self.acme_account_id:
            raise ValidationError("An ACME-issued certificate requires an ACME account.")
