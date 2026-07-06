# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_pki"

# URL path prefixes (and the derived DRF basenames / reverse names) are kept unchanged so the API
# endpoints are stable; only the underlying Python classes/models are Pki-prefixed. Explicit
# basenames pin the reverse names (certificateauthority-detail / certificate-detail) that the
# serializers' HyperlinkedIdentityFields reference, decoupling them from the new model names.
router = NetBoxRouter()
router.register("certificate-authorities", views.PkiCertificateAuthorityViewSet, basename="certificateauthority")
router.register("acme-accounts", views.ACMEAccountViewSet, basename="acmeaccount")
router.register("certificates", views.PkiCertificateViewSet, basename="certificate")

urlpatterns = router.urls
