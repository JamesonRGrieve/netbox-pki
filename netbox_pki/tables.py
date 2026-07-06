# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .models import ACMEAccount, PkiCertificate, PkiCertificateAuthority


class PkiCertificateAuthorityTable(NetBoxTable):
    name = tables.Column(linkify=True)
    ca_type = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name="plugins:netbox_pki:pkicertificateauthority_list")

    class Meta(NetBoxTable.Meta):
        model = PkiCertificateAuthority
        fields = ("pk", "id", "name", "ca_type", "acme_directory_url", "contact_email",
                  "ca_cert_ref", "tags", "created", "last_updated")
        default_columns = ("name", "ca_type", "acme_directory_url", "contact_email")


class ACMEAccountTable(NetBoxTable):
    ca = tables.Column(linkify=True)
    contact_email = tables.Column(linkify=True)
    tags = columns.TagColumn(url_name="plugins:netbox_pki:acmeaccount_list")

    class Meta(NetBoxTable.Meta):
        model = ACMEAccount
        fields = ("pk", "id", "ca", "contact_email", "account_key_ref", "eab_kid", "directory_url",
                  "tags", "created", "last_updated")
        default_columns = ("ca", "contact_email", "eab_kid")


class PkiCertificateTable(NetBoxTable):
    common_name = tables.Column(linkify=True)
    ca = tables.Column(linkify=True)
    acme_account = tables.Column(linkify=True)
    service_instance = tables.Column(linkify=True)
    key_algorithm = columns.ChoiceFieldColumn()
    challenge_type = columns.ChoiceFieldColumn()
    status = columns.ChoiceFieldColumn()
    auto_renew = columns.BooleanColumn()
    is_expiring = columns.BooleanColumn(verbose_name="Expiring")
    tags = columns.TagColumn(url_name="plugins:netbox_pki:pkicertificate_list")

    class Meta(NetBoxTable.Meta):
        model = PkiCertificate
        fields = ("pk", "id", "common_name", "ca", "acme_account", "key_algorithm", "challenge_type",
                  "status", "not_before", "not_after", "auto_renew", "renew_before_days",
                  "is_expiring", "key_ref", "cert_ref", "service_instance", "tags",
                  "created", "last_updated")
        default_columns = ("common_name", "ca", "status", "not_after", "auto_renew", "is_expiring")
