from django.urls import path

from api.production.views import InvoicesProductionDebitNoteApiView, InvoicesProductionCreditNoteApiView, \
    InvoicesProductionApiView

app_name = "production"
urlpatterns = [
    # # path('invoices/', InvoicesListApiView.as_view(), name='invoices'),
    path('invoices-create/', InvoicesProductionApiView.as_view(), name='invoices-create'),
    path('credit-note/', InvoicesProductionCreditNoteApiView.as_view(), name='credit-note'),
    path('debit-note/', InvoicesProductionDebitNoteApiView.as_view(), name='debit-note'),

]