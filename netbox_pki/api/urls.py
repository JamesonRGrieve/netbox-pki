# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_pki"

# The URL path prefixes below are the stable, client-facing API endpoints
# (/certificate-authorities/, /acme-accounts/, /certificates/) — they come from the register()
# prefix and are independent of the DRF basename. The basename derives the internal reverse name;
# it is left to DRF's default (the model name, e.g. pkicertificate) so `{model_name}-detail` reverses
# correctly (NetBox's API test base and the standard route lookup both assume that convention).
router = NetBoxRouter()
router.register("certificate-authorities", views.PkiCertificateAuthorityViewSet)
router.register("acme-accounts", views.ACMEAccountViewSet)
router.register("certificates", views.PkiCertificateViewSet)

urlpatterns = router.urls
