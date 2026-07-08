# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST API CRUD tests against a real DB + real API client (no mocks).

Composes the explicit CRUD mixins (no GraphQL type shipped yet). PkiCertificate create rows use an
INTERNAL CA (no ACME-account requirement) and distinct common names (unique per (common_name, ca));
ACME-account rows use distinct emails on one CA (unique per (ca, contact_email)).
"""
import unittest

from utilities.testing import APIViewTestCases

from netbox_pki.choices import CATypeChoices
from netbox_pki.models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    # Plugin API views register under the `plugins-api:<app_label>-api` namespace;
    # without this override the test base reverses `<app_label>-api:…` (no
    # `plugins-api` prefix) → NoReverseMatch. See utilities/testing/api.py.
    view_namespace = "plugins-api:netbox_pki"

    @classmethod
    def setUpClass(cls):
        if cls is _CRUD:
            raise unittest.SkipTest("abstract API test base")
        super().setUpClass()


class PkiCertificateAuthorityAPITest(_CRUD):
    model = PkiCertificateAuthority
    brief_fields = ["ca_type", "display", "id", "name", "url"]
    bulk_update_data = {"contact_email": "ops@example.com"}

    @classmethod
    def setUpTestData(cls):
        PkiCertificateAuthority.objects.bulk_create([
            PkiCertificateAuthority(name="exist-a", ca_type="internal"),
            PkiCertificateAuthority(name="exist-b", ca_type="external"),
            PkiCertificateAuthority(name="exist-c", ca_type="self_signed"),
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
        ca = PkiCertificateAuthority.objects.create(name="acme-ca", ca_type="acme",
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


class PkiCertificateAPITest(_CRUD):
    model = PkiCertificate
    brief_fields = ["ca", "common_name", "display", "id", "status", "url"]
    bulk_update_data = {"auto_renew": False}

    @classmethod
    def setUpTestData(cls):
        ca = PkiCertificateAuthority.objects.create(name="cert-ca", ca_type=CATypeChoices.INTERNAL)
        PkiCertificate.objects.bulk_create([
            PkiCertificate(common_name=f"exist{i}.example.com", ca=ca, key_ref=f"pki/certs/{i}")
            for i in range(3)
        ])
        cls.create_data = [
            {"common_name": "k1.example.com", "ca": ca.pk, "key_ref": "pki/certs/k1"},
            {"common_name": "k2.example.com", "ca": ca.pk, "key_ref": "pki/certs/k2",
             "sans": ["www.k2.example.com"], "key_algorithm": "rsa2048"},
            {"common_name": "k3.example.com", "ca": ca.pk, "key_ref": "pki/certs/k3",
             "status": "active", "challenge_type": "dns01"},
        ]
