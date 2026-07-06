# netbox-pki — Agent Operating Guide

Adapted from the sibling `../netbox-database` plugin (same engineering + test discipline),
re-targeted to the **PKI layer**.

`netbox-pki` is an **AGPL-3.0** NetBox 4.6 plugin: the **native source of truth for PKI** — the
certificate authorities the estate trusts or issues from, the ACME accounts registered against them,
and the issued certificates (subject, SANs, key algorithm, validity window, renewal policy, status).
It is what the in-house ACME/issuance provider reads to obtain and renew certificates; web-server
vhosts and mail relays then **reference** a certificate's `cert_ref` to terminate TLS. See
**DESIGN.md** for the full data model, the compose boundary, the `netbox_ssl` coexistence note, and
verification owed.

**It composes `netbox-services`, it does not re-model it (the netbox-ai pattern):** a certificate is
(optionally) terminated by a running `netbox_services.ServiceInstance` — `PkiCertificate` **FKs** it,
so `required_plugins = ["netbox_services"]` and the migration depends on
`netbox_services.0001_initial`.

**Coexistence with `netbox_ssl`:** a separate `netbox_ssl` plugin (a passive cert *store*) exists on
the lab NetBox. This plugin is the in-house **ACME/CA-issuance** SoT and stays **standalone** — it
neither depends on nor duplicates `netbox_ssl`. A future integration may reconcile them (DESIGN.md),
but only as an optional bridge, never a hard coupling.

**Secret policy (load-bearing):** private key material, ACME account keys, and EAB secrets are
**never** fields here. Every `*_ref` field (`ca_cert_ref`, `account_key_ref`, `eab_hmac_ref`,
`key_ref`, `cert_ref`) is an **OpenBao path** reference (the netbox-services convention). NetBox
holds the structure; OpenBao holds the secret.

---

## Key Directives / Rules

### DO, ALWAYS:
- If functionality won't work without a parameter, make it a **required positional** parameter.
- Any time you modify a source file, ensure its accompanying test under `netbox_pki/tests/` contains
  **comprehensive tests for the change WITHOUT MOCKS**, so `manage.py test netbox_pki` discovers
  them, and update any `.md` in the same directory that references it.
- Write concise code (avoid obvious comments; one-liners where possible).
- **SPDX header on every source file**: `# SPDX-License-Identifier: AGPL-3.0-or-later`.

### DO NOT, EVER, UNDER ANY CIRCUMSTANCE:
- Make assumptions, or answer with "is likely", "probably", or "might be".
- Store a private key, ACME account key, or any secret **value** in a model field. Only OpenBao path
  references.
- Depend on or duplicate `netbox_ssl` — keep this plugin standalone.
- Duplicate `netbox_services` deployment metadata — FK / reference `ServiceInstance`.
- Use frame-local or thread-local state instead of passing data via parameters.
- Skip a failing test; keep a broken path as a fallback; or re-implement a function in a second
  location to bypass the original. No bandaid fixes.
- **Mock the database, the ORM, the NetBox API test client, or any integration path.** Tests run
  against a **real test database** with real `PkiCertificateAuthority` / `ACMEAccount` /
  `PkiCertificate` rows.

### Python / Django Guidelines:
- Import children of `datetime`: `from datetime import timedelta` — never `import datetime`.
- Package-relative imports inside `netbox_pki` (`from .models import PkiCertificate`); core/sibling
  use the real path (`from netbox_services.api.serializers import ServiceInstanceSerializer`).
- FKs to sibling models in `models.py` use **string labels** (`"netbox_services.ServiceInstance"`) —
  never import them there.
- Models inherit `netbox.models.NetBoxModel` (custom fields, tags, journaling, GraphQL — free).

---

## Architecture (NetBox 4.6 plugin)

| File | Responsibility |
|------|----------------|
| `__init__.py` | `PluginConfig` — name `netbox_pki`, `base_url='pki'`, min/max 4.6, `required_plugins=["netbox_services"]` |
| `choices.py` | `ChoiceSet`s: `CATypeChoices`, `CertStatusChoices`, `KeyAlgorithmChoices`, `ChallengeTypeChoices` |
| `models.py` | the 3 models below (with `clean()` ACME-account rules) |
| `migrations/0001_initial.py` | hand-authored (NetBox disables makemigrations in prod); verify with `makemigrations --check --dry-run`; deps: dcim, extras, netbox_services |
| `api/serializers.py`, `api/views.py`, `api/urls.py` | REST (`NetBoxModelViewSet`, `NetBoxRouter`) — the contract the provider + seeder read; nests netbox_services serializer; exposes `is_expiring` read-only |
| `filtersets.py` | `NetBoxModelFilterSet` per model (explicit `<fk>_id` + `search()`) |
| `tables.py`, `forms.py`, `navigation.py`, `views.py`, `urls.py` | UI (generic NetBox views; `_routes()` helper; PluginMenu groups Certificate Authorities / ACME Accounts / Certificates) |
| `graphql/__init__.py` | placeholder (auto GraphQL via `NetBoxModel`) |

### Model — authorities + accounts + certificates
Model classes are **`Pki`-prefixed** so their inherited `tags` reverse accessors don't clash with
the co-installed `netbox_ssl` plugin's own `Certificate` / `CertificateAuthority` models (E304); the
`verbose_name` UI labels and REST URL paths are unchanged.
- **PkiCertificateAuthority** (UI "Certificate Authority"): `name`(unique)·`ca_type`(acme/internal/external/self_signed)·
  `acme_directory_url`·`contact_email`·`ca_cert_ref`(OpenBao path).
- **ACMEAccount** (FK CA): `contact_email`·`account_key_ref`(OpenBao path)·`eab_kid`·
  `eab_hmac_ref`(OpenBao path)·`directory_url`; unique `(ca, contact_email)`.
- **PkiCertificate** (UI "Certificate"; FK CA `PROTECT`; FK ACMEAccount; FK `netbox_services.ServiceInstance`):
  `common_name`·`sans`(ArrayField)·`key_algorithm`·`challenge_type`·`status`·`not_before`/
  `not_after`·`auto_renew`·`renew_before_days`·`key_ref`(OpenBao path)·`cert_ref`(OpenBao path);
  unique `(common_name, ca)`; `clean()` gates ACME CAs to require a same-CA account; **`is_expiring`
  is a computed property, NOT a stored column**.

---

## Testing (NO MOCKS — real DB, NetBox test framework)

- Tests live in `netbox_pki/tests/` (`test_models.py`, `test_api.py`, `test_filtersets.py`).
- `test_models` covers `clean()` (ACME-account requirement + same-CA), every uniqueness constraint,
  the `is_expiring` property (flagged, within-window, unknown-not_after), `ca` PROTECT, and
  `acme_account` SET_NULL; `test_api` runs the CRUD mixins per model; `test_filtersets` covers FK-id
  scoping, choice filters, and `search()` (incl. SAN search).
- **Run**: `python /opt/netbox/app/netbox/manage.py test netbox_pki --keepdb -v2`.
- **Verification owed (cannot run offline — no NetBox env in the build host):**
  `makemigrations netbox_pki --check --dry-run` on an ephemeral NetBox, and a full test run.
  Re-confirm against the pinned NetBox 4.6: the FK-target serialization
  (`netbox_services.serviceinstance`), the `ArrayField(sans)` surface, the migration `dependencies`,
  and the `netbox_services.api.serializers.ServiceInstanceSerializer` import path. `py_compile`
  passes on every module today.
- **Never skip a failing test** — fix the root cause.

---

## Licensing
- **AGPL-3.0-or-later** (workspace production-IaC standard). SPDX header in every file.
