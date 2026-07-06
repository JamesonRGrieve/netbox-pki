<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# netbox-pki — Design

## 0. Purpose

NetBox is the native source of truth for **PKI** — the certificate authorities the estate trusts or
issues from, the ACME accounts registered against them, and the issued certificates the in-house
ACME/issuance provider obtains and renews. This plugin owns the *issuance intent and lifecycle*, not
the key material: every private key, ACME account key, and EAB secret lives in OpenBao and is
referenced here only by path.

Everything is a real typed column or a child row — no `config_context`, no CustomField data-blob
(the workspace's retired anti-pattern). The renewal knobs (`auto_renew`, `renew_before_days`,
`not_after`) map directly to the reconciler's renewal loop, and the `*_ref` fields map to OpenBao
KV paths.

## 1. Model diagram

```
                              netbox_services.ServiceInstance
                                        ▲ (opt FK, SET_NULL)
                                        │  service_instance
        ┌───────────────────┐  ca (FK)  │
        │ CertificateAuthority│◄─────────┼───────────────┐
        │  name·ca_type·      │          │               │ ca (FK, PROTECT)
        │  acme_directory_url·│    ┌──────┴──────────┐    │
        │  contact_email·     │    │   Certificate   │────┘
        │  ca_cert_ref        │    │  common_name·   │
        └─────────┬───────────┘    │  sans·          │
       ca (FK)    │                │  key_algorithm· │
       CASCADE    ▼                │  challenge_type·│
            ┌───────────┐          │  status·        │
            │ ACMEAccount│◄─────────┤  not_before/after·
            │  contact_  │ acme_    │  auto_renew·    │
            │  email·    │ account  │  renew_before_days·
            │  account_  │ (FK,     │  key_ref·cert_ref
            │  key_ref·  │ SET_NULL)│                 │
            │  eab_kid·  │          └─────────────────┘
            │  eab_hmac_ │
            │  ref·      │   is_expiring = computed property (status/not_after based; NOT a column)
            │  directory_│
            │  url       │
            └───────────┘
```

- **CertificateAuthority** is the trust anchor. `ca_type` selects its class; an `acme` CA carries an
  `acme_directory_url` (Let's Encrypt / ZeroSSL / an internal step-ca). `ca_cert_ref` is an OpenBao
  path to the CA chain.
- **ACMEAccount** registers a `contact_email` against a CA with an `account_key_ref` (OpenBao path).
  `eab_kid` / `eab_hmac_ref` carry External Account Binding for CAs that require it. Unique per
  `(ca, contact_email)`.
- **Certificate** is an issued leaf. `ca` is `PROTECT` (a CA with live certificates cannot be
  deleted out from under them); `acme_account` is `SET_NULL` and, when the CA is ACME, required
  (`clean()`) and must belong to the same CA (`clean()`). `service_instance` is the optional
  composition link to the netbox-services instance that terminates TLS with it (`SET_NULL` — the
  cert SoT survives deleting the instance record). Unique per `(common_name, ca)`.

### is_expiring (computed, not stored)

`Certificate.is_expiring` is a Python property, never a column: `True` when the cert is flagged
`expiring`, or when `not_after` is within `renew_before_days` of now; `False` when `not_after` is
unknown (a pending cert has no validity window yet). It drives the renewal loop without a stored
flag that could drift.

## 2. The compose-with-netbox-services boundary

`Certificate.service_instance` **FKs** `netbox_services.ServiceInstance` — the running service that
terminates TLS with the certificate. The plugin references that instance rather than re-modeling
service metadata. `required_plugins = ["netbox_services"]` + the migration dependency on
`netbox_services.0001_initial` make the dependency hard and fail-fast (the `netbox-ai` pattern).

## 3. Coexistence with netbox_ssl (not a dependency, not a duplicate)

A separate `netbox_ssl` plugin — a passive certificate **store** (upload/track existing PEMs) —
exists on the lab NetBox. `netbox-pki` is the in-house **ACME/CA-issuance** source of truth: it
models the *authorities, accounts, and issuance/renewal lifecycle* that a passive store does not.
The two are deliberately kept **standalone** — `netbox-pki` neither imports, FKs, nor duplicates
`netbox_ssl`.

A future integration may reconcile them (e.g. an issued `Certificate` here materializing a stored
cert in `netbox_ssl`, or `netbox_ssl` becoming the read model for already-present certs). That
reconciliation is **out of scope** for this baseline and, if pursued, must be an explicit,
optional-dependency bridge — never a hard cross-plugin coupling that breaks either plugin standing
alone.

## 4. Secret-ref policy

Private key material, ACME account keys, and EAB HMAC secrets are **never** model fields. The
`*_ref` CharFields (`CertificateAuthority.ca_cert_ref`, `ACMEAccount.account_key_ref` /
`eab_hmac_ref`, `Certificate.key_ref` / `cert_ref`) are **OpenBao path references** — the
`netbox-services` `credential_ref` convention. NetBox holds the structure (which cert, which names,
which CA, which renewal policy, where the key lives); OpenBao holds the key/secret value, resolved
at apply time by the provider. State and change logs therefore never carry plaintext key material.

## 5. Consumer note (how the estate reads this)

- **The in-house ACME/issuance provider** reads `CertificateAuthority` + `ACMEAccount` +
  `Certificate` as the SoT for obtain/renew: register/reuse the ACME account (key from
  `account_key_ref`), solve the `challenge_type`, generate a `key_algorithm` key, issue for
  `common_name` + `sans`, write the private key to `key_ref` and the fullchain to `cert_ref` in
  OpenBao, and stamp `not_before` / `not_after` / `status`. The renewal loop acts on `auto_renew`
  and `is_expiring`.
- **Web-server vhosts and mail relays reference `Certificate.cert_ref`** to terminate TLS — they
  read the fullchain from the OpenBao path this plugin records; they do not own the cert lifecycle.
  The optional `service_instance` FK makes the vhost/relay ⇄ certificate binding explicit.

## 6. Verification owed (cannot run offline — no NetBox env in the build host)

The full NetBox Django test run and `makemigrations netbox_pki --check --dry-run` require a live
NetBox and are **owed**, not yet run here. `python -m py_compile` passes on every module.
Re-confirm against the pinned NetBox 4.6:

- the `Certificate.service_instance` FK target serializes (`netbox_services.serviceinstance`) and
  the migration `dependencies` (`dcim`, `extras`, `netbox_services`) resolve;
- the `ServiceInstanceSerializer` import path (`netbox_services.api.serializers`) is stable;
- the `ArrayField(sans)` migration surface matches the model;
- run `python /opt/netbox/app/netbox/manage.py test netbox_pki --keepdb -v2` green.

Open deep-work items are tracked in `todo.json` (live migration verification, wheel deploy + grant,
the seeder, and the consumer wiring for vhosts / mail relays).
