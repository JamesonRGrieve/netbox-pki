# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic

from . import filtersets, forms, models, tables


class CertificateAuthorityView(generic.ObjectView):
    queryset = models.CertificateAuthority.objects.all()


class CertificateAuthorityListView(generic.ObjectListView):
    queryset = models.CertificateAuthority.objects.all()
    table = tables.CertificateAuthorityTable
    filterset = filtersets.CertificateAuthorityFilterSet
    filterset_form = forms.CertificateAuthorityFilterForm


class CertificateAuthorityEditView(generic.ObjectEditView):
    queryset = models.CertificateAuthority.objects.all()
    form = forms.CertificateAuthorityForm


class CertificateAuthorityDeleteView(generic.ObjectDeleteView):
    queryset = models.CertificateAuthority.objects.all()


class CertificateAuthorityBulkDeleteView(generic.BulkDeleteView):
    queryset = models.CertificateAuthority.objects.all()
    table = tables.CertificateAuthorityTable


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


class CertificateView(generic.ObjectView):
    queryset = models.Certificate.objects.all()


class CertificateListView(generic.ObjectListView):
    queryset = models.Certificate.objects.all()
    table = tables.CertificateTable
    filterset = filtersets.CertificateFilterSet
    filterset_form = forms.CertificateFilterForm


class CertificateEditView(generic.ObjectEditView):
    queryset = models.Certificate.objects.all()
    form = forms.CertificateForm


class CertificateDeleteView(generic.ObjectDeleteView):
    queryset = models.Certificate.objects.all()


class CertificateBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Certificate.objects.all()
    table = tables.CertificateTable
