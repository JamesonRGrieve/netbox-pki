# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic

from . import filtersets, forms, models, tables


class PkiCertificateAuthorityView(generic.ObjectView):
    queryset = models.PkiCertificateAuthority.objects.all()


class PkiCertificateAuthorityListView(generic.ObjectListView):
    queryset = models.PkiCertificateAuthority.objects.all()
    table = tables.PkiCertificateAuthorityTable
    filterset = filtersets.PkiCertificateAuthorityFilterSet
    filterset_form = forms.PkiCertificateAuthorityFilterForm


class PkiCertificateAuthorityEditView(generic.ObjectEditView):
    queryset = models.PkiCertificateAuthority.objects.all()
    form = forms.PkiCertificateAuthorityForm


class PkiCertificateAuthorityDeleteView(generic.ObjectDeleteView):
    queryset = models.PkiCertificateAuthority.objects.all()


class PkiCertificateAuthorityBulkDeleteView(generic.BulkDeleteView):
    queryset = models.PkiCertificateAuthority.objects.all()
    table = tables.PkiCertificateAuthorityTable


class ACMEAccountView(generic.ObjectView):
    queryset = models.ACMEAccount.objects.all()


class ACMEAccountListView(generic.ObjectListView):
    queryset = models.ACMEAccount.objects.all()
    table = tables.ACMEAccountTable
    filterset = filtersets.ACMEAccountFilterSet
    filterset_form = forms.ACMEAccountFilterForm


class ACMEAccountEditView(generic.ObjectEditView):
    queryset = models.ACMEAccount.objects.all()
    form = forms.ACMEAccountForm


class ACMEAccountDeleteView(generic.ObjectDeleteView):
    queryset = models.ACMEAccount.objects.all()


class ACMEAccountBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ACMEAccount.objects.all()
    table = tables.ACMEAccountTable


class PkiCertificateView(generic.ObjectView):
    queryset = models.PkiCertificate.objects.all()


class PkiCertificateListView(generic.ObjectListView):
    queryset = models.PkiCertificate.objects.all()
    table = tables.PkiCertificateTable
    filterset = filtersets.PkiCertificateFilterSet
    filterset_form = forms.PkiCertificateFilterForm


class PkiCertificateEditView(generic.ObjectEditView):
    queryset = models.PkiCertificate.objects.all()
    form = forms.PkiCertificateForm


class PkiCertificateDeleteView(generic.ObjectDeleteView):
    queryset = models.PkiCertificate.objects.all()


class PkiCertificateBulkDeleteView(generic.BulkDeleteView):
    queryset = models.PkiCertificate.objects.all()
    table = tables.PkiCertificateTable
