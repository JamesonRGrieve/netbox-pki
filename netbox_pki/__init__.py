# SPDX-License-Identifier: AGPL-3.0-or-later
"""netbox-pki: NetBox as the native source of truth for **PKI** — the certificate authorities the
estate trusts / issues from, the ACME accounts registered against them, and the issued certificates
(their subject, SANs, key algorithm, validity window, renewal policy, and status). It is what the
in-house ACME/issuance provider reads to obtain and renew certificates; web-server vhosts and mail
relays then **reference** a certificate's ``cert_ref`` to terminate TLS.

**It composes ``netbox-services``, it does not re-model it (the netbox-ai pattern):** a certificate
is (optionally) terminated by a running :class:`netbox_services.ServiceInstance` — ``PkiCertificate``
FKs it, so ``required_plugins = ["netbox_services"]`` and the migration depends on
``netbox_services.0001_initial``.

**Models are ``Pki``-prefixed** (``PkiCertificateAuthority`` / ``PkiCertificate``, with clean
``verbose_name`` UI labels) so their inherited ``tags`` reverse accessors don't collide with the
pre-installed ``netbox_ssl`` plugin's ``Certificate`` / ``CertificateAuthority`` models (E304).

**A separate ``netbox_ssl`` plugin (a passive cert *store*) exists on the lab NetBox.** This
``netbox-pki`` is the in-house **ACME/CA-issuance** source of truth and is deliberately standalone —
it neither depends on nor duplicates ``netbox_ssl``. A future integration may reconcile the two
(see DESIGN.md); until then they do not reference each other.

**Secret policy (load-bearing):** private key material and ACME account keys are **never** fields
here. ``PkiCertificate.key_ref`` / ``PkiCertificate.cert_ref`` and ``ACMEAccount.account_key_ref`` /
``ACMEAccount.eab_hmac_ref`` and ``PkiCertificateAuthority.ca_cert_ref`` are **OpenBao path
references** (the netbox-services ``credential_ref`` convention) — the key/secret value stays in
OpenBao.
"""
from netbox.plugins import PluginConfig

__version__ = "0.0.1"


class NetBoxPKIConfig(PluginConfig):
    name = "netbox_pki"
    verbose_name = "NetBox PKI"
    description = "Native SoT for certificate authorities, ACME accounts, and issued certificates"
    version = __version__
    author = "Jameson"
    base_url = "pki"
    min_version = "4.6.0"
    max_version = "4.6.99"
    # PkiCertificate.service_instance FKs netbox_services.ServiceInstance and the migration depends on
    # netbox_services.0001_initial, so the dependency is hard and fails fast at startup.
    required_plugins = ["netbox_services"]


config = NetBoxPKIConfig
