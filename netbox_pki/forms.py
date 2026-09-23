# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from .choices import CATypeChoices, CertStatusChoices, ChallengeTypeChoices, KeyAlgorithmChoices
from .models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


class PkiCertificateAuthorityForm(NetBoxModelForm):
    fieldsets = (
        FieldSet("name", "ca_type", "contact_email", name="Certificate Authority"),
        FieldSet("acme_directory_url", "ca_cert_ref", "trust_refid", name="ACME / chain"),
    )

    class Meta:
        model = PkiCertificateAuthority
        fields = ["name", "ca_type", "acme_directory_url", "contact_email", "ca_cert_ref", "trust_refid", "tags"]


class ACMEAccountForm(NetBoxModelForm):
    ca = DynamicModelChoiceField(queryset=PkiCertificateAuthority.objects.all())

    fieldsets = (
        FieldSet("ca", "contact_email", "account_key_ref", "directory_url", name="ACME Account"),
        FieldSet("eab_kid", "eab_hmac_ref", name="External Account Binding"),
    )

    class Meta:
        model = ACMEAccount
        fields = ["ca", "contact_email", "account_key_ref", "eab_kid", "eab_hmac_ref",
                  "directory_url", "tags"]


class PkiCertificateForm(NetBoxModelForm):
    ca = DynamicModelChoiceField(queryset=PkiCertificateAuthority.objects.all())
    acme_account = DynamicModelChoiceField(queryset=ACMEAccount.objects.all(), required=False)

    fieldsets = (
        FieldSet("common_name", "sans", "ca", "acme_account", name="Subject / issuer"),
        FieldSet("key_algorithm", "challenge_type", "status", name="Issuance"),
        FieldSet("not_before", "not_after", "auto_renew", "renew_before_days", name="Validity / renewal"),
        FieldSet("key_ref", "cert_ref", "service_instance", name="Storage / binding"),
    )

    class Meta:
        model = PkiCertificate
        fields = ["common_name", "sans", "ca", "acme_account", "key_algorithm", "challenge_type",
                  "status", "not_before", "not_after", "auto_renew", "renew_before_days",
                  "key_ref", "cert_ref", "service_instance", "tags"]


class PkiCertificateAuthorityFilterForm(NetBoxModelFilterSetForm):
    model = PkiCertificateAuthority
    ca_type = forms.MultipleChoiceField(choices=CATypeChoices, required=False)
    tag = TagFilterField(PkiCertificateAuthority)


class ACMEAccountFilterForm(NetBoxModelFilterSetForm):
    model = ACMEAccount
    ca_id = DynamicModelMultipleChoiceField(
        queryset=PkiCertificateAuthority.objects.all(), required=False, label="CA"
    )
    tag = TagFilterField(ACMEAccount)


class PkiCertificateFilterForm(NetBoxModelFilterSetForm):
    model = PkiCertificate
    ca_id = DynamicModelMultipleChoiceField(
        queryset=PkiCertificateAuthority.objects.all(), required=False, label="CA"
    )
    acme_account_id = DynamicModelMultipleChoiceField(
        queryset=ACMEAccount.objects.all(), required=False, label="ACME account"
    )
    key_algorithm = forms.MultipleChoiceField(choices=KeyAlgorithmChoices, required=False)
    challenge_type = forms.MultipleChoiceField(choices=ChallengeTypeChoices, required=False)
    status = forms.MultipleChoiceField(choices=CertStatusChoices, required=False)
    auto_renew = forms.NullBooleanField(required=False)
    tag = TagFilterField(PkiCertificate)
