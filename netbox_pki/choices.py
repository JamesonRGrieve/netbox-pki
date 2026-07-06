# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choice sets for the PKI models. Values match the issuance-provider tokens verbatim (CA class,
certificate lifecycle status, key algorithm, and ACME challenge type)."""
from utilities.choices import ChoiceSet


class CATypeChoices(ChoiceSet):
    """Class of certificate authority a :class:`PkiCertificateAuthority` represents. ``acme`` CAs carry
    an ``acme_directory_url`` (Let's Encrypt / ZeroSSL / an internal step-ca); ``internal`` is a
    privately-run CA; ``external`` is a commercial/public CA outside our control; ``self_signed`` is
    an ad-hoc self-signed root."""
    INTERNAL = "internal"
    ACME = "acme"
    EXTERNAL = "external"
    SELF_SIGNED = "self_signed"
    CHOICES = [
        (INTERNAL, "Internal", "blue"),
        (ACME, "ACME", "green"),
        (EXTERNAL, "External", "orange"),
        (SELF_SIGNED, "Self-signed", "gray"),
    ]


class CertStatusChoices(ChoiceSet):
    """Lifecycle status of an issued :class:`PkiCertificate`."""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CHOICES = [
        (PENDING, "Pending", "gray"),
        (ACTIVE, "Active", "green"),
        (EXPIRING, "Expiring", "orange"),
        (EXPIRED, "Expired", "red"),
        (REVOKED, "Revoked", "black"),
    ]


class KeyAlgorithmChoices(ChoiceSet):
    """Key algorithm + size the certificate's private key uses."""
    RSA2048 = "rsa2048"
    RSA4096 = "rsa4096"
    ECDSA_P256 = "ecdsa_p256"
    ECDSA_P384 = "ecdsa_p384"
    CHOICES = [
        (RSA2048, "RSA 2048", "blue"),
        (RSA4096, "RSA 4096", "indigo"),
        (ECDSA_P256, "ECDSA P-256", "green"),
        (ECDSA_P384, "ECDSA P-384", "teal"),
    ]


class ChallengeTypeChoices(ChoiceSet):
    """ACME challenge type used to validate control of the certificate's names."""
    HTTP01 = "http01"
    DNS01 = "dns01"
    TLSALPN01 = "tlsalpn01"
    CHOICES = [
        (HTTP01, "HTTP-01", "blue"),
        (DNS01, "DNS-01", "green"),
        (TLSALPN01, "TLS-ALPN-01", "purple"),
    ]
