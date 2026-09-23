<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# netbox-pki

A NetBox 4.6 plugin: the **native source of truth for PKI** — the certificate authorities the estate
trusts or issues from, the ACME accounts registered against them, and the issued certificates (their
subject, SANs, key algorithm, validity window, renewal policy, and status).

It is what the in-house ACME/issuance provider reads to obtain and renew certificates. Web-server
vhosts and mail relays then **reference** a certificate's `cert_ref` to terminate TLS.

## Scope

- **In scope:** certificate authorities (ACME / internal / external / self-signed), ACME accounts
  (incl. External Account Binding), and issued certificates with their renewal policy.
- **Out of scope:** private key / secret **values** (OpenBao owns them — this plugin stores only
  path references), and the passive cert *store* provided by the separate `netbox_ssl` plugin (see
  below — not depended on, not duplicated).

## Composes netbox-services

A certificate is (optionally) terminated by a running `netbox_services.ServiceInstance`.
`PkiCertificate` FKs it, so `PluginConfig.required_plugins = ["netbox_services"]` and the migration
depends on `netbox_services.0001_initial`. This plugin references, it does not re-model (the
`netbox-ai` pattern).

## Relationship to netbox_ssl

A separate `netbox_ssl` plugin (a passive certificate *store*) exists on the lab NetBox.
`netbox-pki` is the in-house **ACME/CA-issuance** source of truth and is deliberately standalone: it
neither depends on nor duplicates `netbox_ssl`. A future integration may reconcile the two — see
DESIGN.md. The model classes are **`Pki`-prefixed** (`PkiCertificateAuthority` / `PkiCertificate`)
precisely so their inherited `tags` reverse accessors don't collide with `netbox_ssl`'s own
`Certificate` / `CertificateAuthority` models (Django system check E304); their `verbose_name` UI
labels stay "Certificate Authority" / "Certificate".

## Model

- **PkiCertificateAuthority** (UI: "Certificate Authority") — `name`, `ca_type` (acme / internal /
  external / self_signed), `acme_directory_url` (for ACME CAs), `contact_email`, `ca_cert_ref`
  (**OpenBao path** to the CA chain), `trust_refid` (the fixed appliance trust-store id, e.g. an
  OPNsense refid a frontend's client-auth CA list references; unique when set).
- **ACMEAccount** (FK CA) — `contact_email`, `account_key_ref` (**OpenBao path**), `eab_kid` /
  `eab_hmac_ref` (External Account Binding), `directory_url`. Unique per `(ca, contact_email)`.
- **PkiCertificate** (UI: "Certificate"; FK CA `PROTECT`; FK ACMEAccount; FK
  `netbox_services.ServiceInstance`) — `common_name`, `sans`, `key_algorithm`, `challenge_type`,
  `status`, `not_before` / `not_after`, `auto_renew`, `renew_before_days`, `key_ref` / `cert_ref`
  (**OpenBao paths**). Unique per `(common_name, ca)`. Exposes a computed `is_expiring` property.

All models inherit `NetBoxModel` (custom fields, tags, change logging, GraphQL, REST API).

## Secret policy

Private key material and ACME account keys are **never** fields here. Every `*_ref` field is an
**OpenBao path reference** (the `netbox-services` convention). NetBox holds the structure; OpenBao
holds the key/secret value, resolved at apply time by the provider.

## Install

```bash
uv pip install --python /opt/netbox/venv/bin/python netbox-pki   # or: pip install -e .
# add "netbox_pki" to PLUGINS in configuration.py (netbox_services must be enabled too)
python manage.py migrate netbox_pki
python manage.py collectstatic --no-input
systemctl restart netbox netbox-rq
```

## Develop / test

Tests run against a **real NetBox test database** (no mocks) via NetBox's Django test framework.

```bash
python /opt/netbox/app/netbox/manage.py test netbox_pki --keepdb -v2
```

## License

AGPL-3.0-or-later.
