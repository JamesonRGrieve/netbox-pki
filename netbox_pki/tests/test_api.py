# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (no GraphQL type shipped yet). Certificate create rows use an
INTERNAL CA (no ACME-account requirement) and distinct common names (unique per (common_name, ca));
ACME-account rows use distinct emails on one CA (unique per (ca, contact_email)).
"""
from utilities.testing import APIViewTestCases

from netbox_pki.choices import CATypeChoices
from netbox_pki.models import ACMEAccount, Certificate, CertificateAuthority


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    pass


class CertificateAuthorityAPITest(_CRUD):
    model = CertificateAuthority
    brief_fields = ["ca_type", "display", "id", "name", "url"]
    bulk_update_data = {"contact_email": "ops@example.com"}

    @classmethod
    def setUpTestData(cls):
        CertificateAuthority.objects.bulk_create([
            CertificateAuthority(name="exist-a", ca_type="internal"),
            CertificateAuthority(name="exist-b", ca_type="external"),
            CertificateAuthority(name="exist-c", ca_type="self_signed"),
        ])
        cls.create_data = [
            {"name": "ca-a", "ca_type": "acme", "acme_directory_url": "https://acme.example/dir"},
            {"name": "ca-b", "ca_type": "internal", "contact_email": "pki@example.com"},
            {"name": "ca-c", "ca_type": "external"},
        ]


class ACMEAccountAPITest(_CRUD):
    model = ACMEAccount
    brief_fields = ["ca", "contact_email", "display", "id", "url"]
    bulk_update_data = {"eab_kid": "kid-rotated"}

    @classmethod
    def setUpTestData(cls):
        ca = CertificateAuthority.objects.create(name="acme-ca", ca_type="acme",
                                                 acme_directory_url="https://acme.example/dir")
        ACMEAccount.objects.bulk_create([
            ACMEAccount(ca=ca, contact_email=f"e{i}@example.com", account_key_ref=f"pki/acme/{i}")
            for i in range(3)
        ])
        cls.create_data = [
            {"ca": ca.pk, "contact_email": "k1@example.com", "account_key_ref": "pki/acme/k1"},
            {"ca": ca.pk, "contact_email": "k2@example.com", "account_key_ref": "pki/acme/k2", "eab_kid": "kid2"},
            {"ca": ca.pk, "contact_email": "k3@example.com", "account_key_ref": "pki/acme/k3"},
        ]


class CertificateAPITest(_CRUD):
    model = Certificate
    brief_fields = ["ca", "common_name", "display", "id", "status", "url"]
    bulk_update_data = {"auto_renew": False}

    @classmethod
    def setUpTestData(cls):
        ca = CertificateAuthority.objects.create(name="cert-ca", ca_type=CATypeChoices.INTERNAL)
        Certificate.objects.bulk_create([
            Certificate(common_name=f"exist{i}.example.com", ca=ca, key_ref=f"pki/certs/{i}")
            for i in range(3)
        ])
        cls.create_data = [
            {"common_name": "k1.example.com", "ca": ca.pk, "key_ref": "pki/certs/k1"},
            {"common_name": "k2.example.com", "ca": ca.pk, "key_ref": "pki/certs/k2",
             "sans": ["www.k2.example.com"], "key_algorithm": "rsa2048"},
            {"common_name": "k3.example.com", "ca": ca.pk, "key_ref": "pki/certs/k3",
             "status": "active", "challenge_type": "dns01"},
        ]
