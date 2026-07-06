# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.serializers import NetBoxModelSerializer
from netbox_services.api.serializers import ServiceInstanceSerializer
from rest_framework import serializers

from ..models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


class PkiCertificateAuthoritySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_pki-api:certificateauthority-detail")

    class Meta:
        model = PkiCertificateAuthority
        fields = [
            "id", "url", "display", "name", "ca_type", "acme_directory_url", "contact_email",
            "ca_cert_ref", "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "ca_type"]


class ACMEAccountSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_pki-api:acmeaccount-detail")
    ca = PkiCertificateAuthoritySerializer(nested=True)

    class Meta:
        model = ACMEAccount
        fields = [
            "id", "url", "display", "ca", "contact_email", "account_key_ref", "eab_kid",
            "eab_hmac_ref", "directory_url", "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "ca", "contact_email"]


class PkiCertificateSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_pki-api:certificate-detail")
    ca = PkiCertificateAuthoritySerializer(nested=True)
    acme_account = ACMEAccountSerializer(nested=True, required=False, allow_null=True)
    service_instance = ServiceInstanceSerializer(nested=True, required=False, allow_null=True)
    is_expiring = serializers.BooleanField(read_only=True)

    class Meta:
        model = PkiCertificate
        fields = [
            "id", "url", "display", "common_name", "sans", "ca", "acme_account", "key_algorithm",
            "challenge_type", "status", "not_before", "not_after", "auto_renew", "renew_before_days",
            "is_expiring", "key_ref", "cert_ref", "service_instance",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "common_name", "ca", "status"]
