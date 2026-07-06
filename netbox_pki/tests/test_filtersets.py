# SPDX-License-Identifier: AGPL-3.0-or-later
"""FilterSet tests against a real DB (no mocks): FK-id scoping, choice filters, and search()."""
from django.test import TestCase

from netbox_pki.choices import CATypeChoices, CertStatusChoices, KeyAlgorithmChoices
from netbox_pki.filtersets import ACMEAccountFilterSet, PkiCertificateAuthorityFilterSet, PkiCertificateFilterSet
from netbox_pki.models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


class PkiCertificateAuthorityFilterSetTest(TestCase):
    queryset = PkiCertificateAuthority.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.ca1 = PkiCertificateAuthority.objects.create(
            name="le", ca_type=CATypeChoices.ACME, acme_directory_url="https://acme.le/dir"
        )
        cls.ca2 = PkiCertificateAuthority.objects.create(name="corp-root", ca_type=CATypeChoices.INTERNAL)

    def test_ca_type(self):
        self.assertEqual(PkiCertificateAuthorityFilterSet({"ca_type": ["acme"]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(PkiCertificateAuthorityFilterSet({"q": "corp"}, self.queryset).qs.count(), 1)


class ACMEAccountFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca1 = PkiCertificateAuthority.objects.create(name="acme1", ca_type=CATypeChoices.ACME)
        cls.ca2 = PkiCertificateAuthority.objects.create(name="acme2", ca_type=CATypeChoices.ACME)
        ACMEAccount.objects.bulk_create([
            ACMEAccount(ca=cls.ca1, contact_email="a@example.com", account_key_ref="pki/a"),
            ACMEAccount(ca=cls.ca1, contact_email="b@example.com", account_key_ref="pki/b"),
            ACMEAccount(ca=cls.ca2, contact_email="c@example.com", account_key_ref="pki/c"),
        ])

    def test_ca_scope(self):
        qs = ACMEAccount.objects.all()
        self.assertEqual(ACMEAccountFilterSet({"ca_id": [self.ca1.pk]}, qs).qs.count(), 2)

    def test_search(self):
        self.assertEqual(ACMEAccountFilterSet({"q": "c@example.com"}, ACMEAccount.objects.all()).qs.count(), 1)


class PkiCertificateFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = PkiCertificateAuthority.objects.create(name="int", ca_type=CATypeChoices.INTERNAL)
        PkiCertificate.objects.bulk_create([
            PkiCertificate(common_name="alpha.example.com", ca=cls.ca, key_ref="pki/1",
                        status=CertStatusChoices.ACTIVE, key_algorithm=KeyAlgorithmChoices.RSA2048),
            PkiCertificate(common_name="beta.example.com", ca=cls.ca, key_ref="pki/2",
                        status=CertStatusChoices.EXPIRED, sans=["www.beta.example.com"]),
            PkiCertificate(common_name="gamma.example.com", ca=cls.ca, key_ref="pki/3",
                        status=CertStatusChoices.ACTIVE),
        ])

    def test_ca_scope(self):
        self.assertEqual(PkiCertificateFilterSet({"ca_id": [self.ca.pk]}, PkiCertificate.objects.all()).qs.count(), 3)

    def test_status(self):
        self.assertEqual(PkiCertificateFilterSet({"status": ["active"]}, PkiCertificate.objects.all()).qs.count(), 2)

    def test_key_algorithm(self):
        self.assertEqual(PkiCertificateFilterSet({"key_algorithm": ["rsa2048"]}, PkiCertificate.objects.all()).qs.count(), 1)

    def test_search_common_name(self):
        self.assertEqual(PkiCertificateFilterSet({"q": "gamma"}, PkiCertificate.objects.all()).qs.count(), 1)

    def test_search_san(self):
        self.assertEqual(PkiCertificateFilterSet({"q": "www.beta"}, PkiCertificate.objects.all()).qs.count(), 1)
