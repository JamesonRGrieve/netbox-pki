# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import ACMEAccount, Certificate, CertificateAuthority
from .serializers import ACMEAccountSerializer, CertificateAuthoritySerializer, CertificateSerializer


class CertificateAuthorityViewSet(NetBoxModelViewSet):
    queryset = CertificateAuthority.objects.prefetch_related("tags")
    serializer_class = CertificateAuthoritySerializer
    filterset_class = filtersets.CertificateAuthorityFilterSet


class ACMEAccountViewSet(NetBoxModelViewSet):
    queryset = ACMEAccount.objects.prefetch_related("ca", "tags")
    serializer_class = ACMEAccountSerializer
    filterset_class = filtersets.ACMEAccountFilterSet


class CertificateViewSet(NetBoxModelViewSet):
    queryset = Certificate.objects.prefetch_related("ca", "acme_account", "service_instance", "tags")
    serializer_class = CertificateSerializer
    filterset_class = filtersets.CertificateFilterSet
