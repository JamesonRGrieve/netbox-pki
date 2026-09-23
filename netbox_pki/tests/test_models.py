# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model tests against a real DB (no mocks): creation, str, clean() rules, constraints, the
is_expiring computed property, PROTECT, and cascades."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from netbox_pki.choices import CATypeChoices, CertStatusChoices, ChallengeTypeChoices, KeyAlgorithmChoices
from netbox_pki.models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


def make_ca(name="le", ca_type=CATypeChoices.ACME, **kw):
    kw.setdefault("acme_directory_url", "https://acme.example/directory" if ca_type == CATypeChoices.ACME else "")
    return PkiCertificateAuthority.objects.create(name=name, ca_type=ca_type, **kw)


def make_account(ca, email="admin@example.com"):
    return ACMEAccount.objects.create(ca=ca, contact_email=email, account_key_ref="pki/acme/key")


def make_cert(ca, name="www.example.com", account=None, **kw):
    kw.setdefault("key_ref", "pki/certs/www/key")
    return PkiCertificate.objects.create(common_name=name, ca=ca, acme_account=account, **kw)


class PkiCertificateAuthorityModelTest(TestCase):
    def test_create_str_url_and_color(self):
        ca = make_ca("internal-ca", CATypeChoices.INTERNAL)
        self.assertEqual(str(ca), "internal-ca (internal)")
        self.assertIn("/plugins/pki/certificate-authorities/", ca.get_absolute_url())
        self.assertEqual(ca.get_ca_type_color(), "blue")

    def test_name_unique(self):
        make_ca("dup", CATypeChoices.INTERNAL)
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_ca("dup", CATypeChoices.EXTERNAL)

    def test_trust_refid_defaults_blank(self):
        self.assertEqual(make_ca("no-store", CATypeChoices.INTERNAL).trust_refid, "")

    def test_trust_refid_valid_value_saves(self):
        ca = make_ca("stored", CATypeChoices.SELF_SIGNED, trust_refid="0e2133fa11ca0")
        ca.full_clean()
        self.assertEqual(PkiCertificateAuthority.objects.get(pk=ca.pk).trust_refid, "0e2133fa11ca0")

    def test_trust_refid_rejects_non_refid(self):
        for bad in ("0E2133FA11CA0", "0e2133fa11ca", "0e2133fa11ca00", "zz2133fa11ca0"):
            ca = PkiCertificateAuthority(name=f"bad-{bad}", ca_type=CATypeChoices.INTERNAL, trust_refid=bad)
            with self.assertRaises(ValidationError):
                ca.full_clean()

    def test_trust_refid_unique_when_set(self):
        make_ca("first", CATypeChoices.INTERNAL, trust_refid="6a9ac549cc8d0")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_ca("second", CATypeChoices.EXTERNAL, trust_refid="6a9ac549cc8d0")

    def test_blank_trust_refid_not_unique(self):
        make_ca("blank-a", CATypeChoices.INTERNAL)
        make_ca("blank-b", CATypeChoices.EXTERNAL)
        self.assertEqual(PkiCertificateAuthority.objects.filter(trust_refid="").count(), 2)


class ACMEAccountModelTest(TestCase):
    def test_create_str_url_and_ref_is_path(self):
        ca = make_ca()
        acct = make_account(ca)
        self.assertEqual(str(acct), "admin@example.com @ le")
        self.assertEqual(acct.account_key_ref, "pki/acme/key")  # a path, not the key
        self.assertIn("/plugins/pki/acme-accounts/", acct.get_absolute_url())

    def test_unique_ca_contact_email(self):
        ca = make_ca()
        make_account(ca, "a@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_account(ca, "a@example.com")

    def test_same_email_different_ca_allowed(self):
        make_account(make_ca("ca-a"), "shared@example.com")
        make_account(make_ca("ca-b"), "shared@example.com")
        self.assertEqual(ACMEAccount.objects.filter(contact_email="shared@example.com").count(), 2)


class PkiCertificateModelTest(TestCase):
    def test_create_defaults_str_url_and_colors(self):
        ca = make_ca()
        acct = make_account(ca)
        cert = make_cert(ca, account=acct, sans=["www.example.com", "example.com"])
        self.assertEqual(cert.key_algorithm, KeyAlgorithmChoices.ECDSA_P256)
        self.assertEqual(cert.challenge_type, ChallengeTypeChoices.HTTP01)
        self.assertEqual(cert.status, CertStatusChoices.PENDING)
        self.assertTrue(cert.auto_renew)
        self.assertEqual(cert.renew_before_days, 30)
        self.assertEqual(str(cert), "www.example.com [le]")
        self.assertIn("/plugins/pki/certificates/", cert.get_absolute_url())
        self.assertEqual(cert.get_status_color(), "gray")
        self.assertEqual(cert.get_key_algorithm_color(), "green")
        self.assertEqual(cert.get_challenge_type_color(), "blue")
        self.assertEqual(cert.sans, ["www.example.com", "example.com"])

    def test_unique_common_name_ca(self):
        ca = make_ca()
        acct = make_account(ca)
        make_cert(ca, "dup.example.com", account=acct)
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_cert(ca, "dup.example.com", account=acct)

    def test_same_common_name_different_ca_allowed(self):
        make_cert(make_ca("ca-a", CATypeChoices.INTERNAL), "x.example.com")
        make_cert(make_ca("ca-b", CATypeChoices.INTERNAL), "x.example.com")
        self.assertEqual(PkiCertificate.objects.filter(common_name="x.example.com").count(), 2)

    def test_is_expiring_flagged_status(self):
        cert = make_cert(make_ca("s", CATypeChoices.INTERNAL), status=CertStatusChoices.EXPIRING)
        self.assertTrue(cert.is_expiring)

    def test_is_expiring_within_window(self):
        ca = make_ca("w", CATypeChoices.INTERNAL)
        soon = make_cert(ca, "soon.example.com", not_after=timezone.now() + timedelta(days=10))
        self.assertTrue(soon.is_expiring)  # inside the 30-day renew window
        far = make_cert(ca, "far.example.com", not_after=timezone.now() + timedelta(days=90))
        self.assertFalse(far.is_expiring)

    def test_is_expiring_unknown_not_after_is_false(self):
        cert = make_cert(make_ca("u", CATypeChoices.INTERNAL))  # pending, not_after None
        self.assertFalse(cert.is_expiring)

    def test_clean_acme_ca_requires_account(self):
        ca = make_ca()  # ACME
        cert = PkiCertificate(common_name="need.example.com", ca=ca, key_ref="pki/k")
        with self.assertRaises(ValidationError):
            cert.clean()

    def test_clean_account_must_match_ca(self):
        ca1, ca2 = make_ca("ca1"), make_ca("ca2")
        acct = make_account(ca2)
        cert = PkiCertificate(common_name="mismatch.example.com", ca=ca1, acme_account=acct, key_ref="pki/k")
        with self.assertRaises(ValidationError):
            cert.clean()

    def test_clean_internal_ca_no_account_ok(self):
        cert = PkiCertificate(common_name="ok.example.com", ca=make_ca("int", CATypeChoices.INTERNAL), key_ref="pki/k")
        cert.clean()  # no raise

    def test_ca_protect_on_delete_with_certs(self):
        ca = make_ca("protect", CATypeChoices.INTERNAL)
        make_cert(ca, "held.example.com")
        with self.assertRaises(ProtectedError):
            ca.delete()

    def test_acme_account_set_null_on_delete(self):
        ca = make_ca()
        acct = make_account(ca)
        cert = make_cert(ca, "orphan.example.com", account=acct)
        acct.delete()
        cert.refresh_from_db()
        self.assertIsNone(cert.acme_account_id)
