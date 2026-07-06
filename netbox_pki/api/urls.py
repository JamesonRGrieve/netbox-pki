# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_pki"

router = NetBoxRouter()
router.register("certificate-authorities", views.CertificateAuthorityViewSet)
router.register("acme-accounts", views.ACMEAccountViewSet)
router.register("certificates", views.CertificateViewSet)

urlpatterns = router.urls
