# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from .choices import CATypeChoices, CertStatusChoices, ChallengeTypeChoices, KeyAlgorithmChoices
from .models import ACMEAccount, PkiCertificate, PkiCertificateAuthority

# Explicit FK filters: django-filter does NOT derive `<fk>_id` from a bare FK in Meta.fields, so
# `?ca_id=` would be silently ignored. NetBox convention is `<fk>_id` (by PK) + `<fk>` (name).


class PkiCertificateAuthorityFilterSet(NetBoxModelFilterSet):
    ca_type = django_filters.MultipleChoiceFilter(choices=CATypeChoices)

    class Meta:
        model = PkiCertificateAuthority
        fields = ["id", "name", "acme_directory_url", "contact_email", "ca_cert_ref", "trust_refid"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(contact_email__icontains=value)
            | Q(acme_directory_url__icontains=value)
        )


class ACMEAccountFilterSet(NetBoxModelFilterSet):
    ca_id = django_filters.ModelMultipleChoiceFilter(
        field_name="ca", queryset=PkiCertificateAuthority.objects.all(), label="CA (ID)"
    )
    ca = django_filters.ModelMultipleChoiceFilter(
        field_name="ca__name", to_field_name="name",
        queryset=PkiCertificateAuthority.objects.all(), label="CA (name)",
    )

    class Meta:
        model = ACMEAccount
        fields = ["id", "contact_email", "account_key_ref", "eab_kid", "directory_url"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(contact_email__icontains=value) | Q(ca__name__icontains=value)
            | Q(eab_kid__icontains=value)
        )


class PkiCertificateFilterSet(NetBoxModelFilterSet):
    ca_id = django_filters.ModelMultipleChoiceFilter(
        field_name="ca", queryset=PkiCertificateAuthority.objects.all(), label="CA (ID)"
    )
    ca = django_filters.ModelMultipleChoiceFilter(
        field_name="ca__name", to_field_name="name",
        queryset=PkiCertificateAuthority.objects.all(), label="CA (name)",
    )
    acme_account_id = django_filters.ModelMultipleChoiceFilter(
        field_name="acme_account", queryset=ACMEAccount.objects.all(), label="ACME account (ID)"
    )
    key_algorithm = django_filters.MultipleChoiceFilter(choices=KeyAlgorithmChoices)
    challenge_type = django_filters.MultipleChoiceFilter(choices=ChallengeTypeChoices)
    status = django_filters.MultipleChoiceFilter(choices=CertStatusChoices)

    class Meta:
        model = PkiCertificate
        fields = ["id", "common_name", "auto_renew", "renew_before_days", "key_ref", "cert_ref",
                  "service_instance_id"]

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(common_name__icontains=value) | Q(sans__icontains=value)
            | Q(ca__name__icontains=value)
        )
