from django.urls import path

from api.sandbox.views import InvoicesSandboxCreditNoteApiView, InvoicesSandboxApiView, InvoicesSandboxDebitNoteApiView, \
    ValidateOtpApiView, SandboxCredentialsView, ValidateSpecificActionApiView, ResubmitInvoiceAPIView

app_name = "sandbox"
urlpatterns = [
    # path('invoices/', InvoicesListApiView.as_view(), name='invoices'),
    path('invoices-create/', InvoicesSandboxApiView.as_view(), name='invoices-create'),
    path('credit-note/', InvoicesSandboxCreditNoteApiView.as_view(), name='credit-note'),
    path('debit-note/', InvoicesSandboxDebitNoteApiView.as_view(), name='debit-note'),
    path('generate-credentials/', ValidateOtpApiView.as_view(), name='debit-note'),
    path('specific-credentials/', ValidateSpecificActionApiView.as_view(), name='debit-note'),
    path('credentials/', SandboxCredentialsView.as_view(), name='debit-note'),

    path('resubmit-invoice/', ResubmitInvoiceAPIView.as_view(), name='resubmit-invoice'),

]
