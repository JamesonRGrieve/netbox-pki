# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import ACMEAccount, PkiCertificate, PkiCertificateAuthority
from .serializers import ACMEAccountSerializer, PkiCertificateAuthoritySerializer, PkiCertificateSerializer


class PkiCertificateAuthorityViewSet(NetBoxModelViewSet):
    queryset = PkiCertificateAuthority.objects.prefetch_related("tags")
    serializer_class = PkiCertificateAuthoritySerializer
    filterset_class = filtersets.PkiCertificateAuthorityFilterSet


class ACMEAccountViewSet(NetBoxModelViewSet):
    queryset = ACMEAccount.objects.prefetch_related("ca", "tags")
    serializer_class = ACMEAccountSerializer
    filterset_class = filtersets.ACMEAccountFilterSet


class PkiCertificateViewSet(NetBoxModelViewSet):
    queryset = PkiCertificate.objects.prefetch_related("ca", "acme_account", "service_instance", "tags")
    serializer_class = PkiCertificateSerializer
    filterset_class = filtersets.PkiCertificateFilterSet
