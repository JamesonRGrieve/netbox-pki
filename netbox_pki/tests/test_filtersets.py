# SPDX-License-Identifier: AGPL-3.0-or-later
"""FilterSet tests against a real DB (no mocks): FK-id scoping, choice filters, and search()."""
from django.test import TestCase

from netbox_pki.choices import CATypeChoices, CertStatusChoices, KeyAlgorithmChoices
from netbox_pki.filtersets import ACMEAccountFilterSet, CertificateAuthorityFilterSet, CertificateFilterSet
from netbox_pki.models import ACMEAccount, Certificate, CertificateAuthority


class CertificateAuthorityFilterSetTest(TestCase):
    queryset = CertificateAuthority.objects.all()

    @classmethod
    def setUpTestData(cls):
        cls.ca1 = CertificateAuthority.objects.create(
            name="le", ca_type=CATypeChoices.ACME, acme_directory_url="https://acme.le/dir"
        )
        cls.ca2 = CertificateAuthority.objects.create(name="corp-root", ca_type=CATypeChoices.INTERNAL)

    def test_ca_type(self):
        self.assertEqual(CertificateAuthorityFilterSet({"ca_type": ["acme"]}, self.queryset).qs.count(), 1)

    def test_search(self):
        self.assertEqual(CertificateAuthorityFilterSet({"q": "corp"}, self.queryset).qs.count(), 1)


class ACMEAccountFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca1 = CertificateAuthority.objects.create(name="acme1", ca_type=CATypeChoices.ACME)
        cls.ca2 = CertificateAuthority.objects.create(name="acme2", ca_type=CATypeChoices.ACME)
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


class CertificateFilterSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ca = CertificateAuthority.objects.create(name="int", ca_type=CATypeChoices.INTERNAL)
        Certificate.objects.bulk_create([
            Certificate(common_name="alpha.example.com", ca=cls.ca, key_ref="pki/1",
                        status=CertStatusChoices.ACTIVE, key_algorithm=KeyAlgorithmChoices.RSA2048),
            Certificate(common_name="beta.example.com", ca=cls.ca, key_ref="pki/2",
                        status=CertStatusChoices.EXPIRED, sans=["www.beta.example.com"]),
            Certificate(common_name="gamma.example.com", ca=cls.ca, key_ref="pki/3",
                        status=CertStatusChoices.ACTIVE),
        ])

    def test_ca_scope(self):
        self.assertEqual(CertificateFilterSet({"ca_id": [self.ca.pk]}, Certificate.objects.all()).qs.count(), 3)

    def test_status(self):
        self.assertEqual(CertificateFilterSet({"status": ["active"]}, Certificate.objects.all()).qs.count(), 2)

    def test_key_algorithm(self):
        self.assertEqual(CertificateFilterSet({"key_algorithm": ["rsa2048"]}, Certificate.objects.all()).qs.count(), 1)

    def test_search_common_name(self):
        self.assertEqual(CertificateFilterSet({"q": "gamma"}, Certificate.objects.all()).qs.count(), 1)

    def test_search_san(self):
        self.assertEqual(CertificateFilterSet({"q": "www.beta"}, Certificate.objects.all()).qs.count(), 1)
