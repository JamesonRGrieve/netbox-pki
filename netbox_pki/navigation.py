# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(model, label):
    return PluginMenuItem(
        link=f"plugins:netbox_pki:{model}_list",
        link_text=label,
        buttons=[
            PluginMenuButton(f"plugins:netbox_pki:{model}_add", "Add", "mdi mdi-plus-thick")
        ],
    )


menu = PluginMenu(
    label="PKI",
    groups=(
        ("Certificate Authorities", (_item("pkicertificateauthority", "Certificate Authorities"),)),
        ("ACME Accounts", (_item("acmeaccount", "ACME Accounts"),)),
        ("Certificates", (_item("pkicertificate", "Certificates"),)),
    ),
    icon_class="mdi mdi-certificate",
)
