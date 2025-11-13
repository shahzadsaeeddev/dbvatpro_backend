from django.urls import path
from rest_framework.routers import DefaultRouter


from .views import *

app_name = 'api'
router = DefaultRouter()
router.register(r'locations', LocationView)

urlpatterns = [
    path('', Index, name='index'),
    # EGS Location Create post & patch
    path('egs-location/', BusinessLocationListCreateView.as_view(), name='egs-location'),
    path('egs-location-update/', BusinessLocationUpdateView.as_view(), name='egs-location'),

    # Supplier create post & patch
    path('supplier/', SupplierDetailsCreateApiView.as_view(), name='supplier'),
    path('supplier-update/', SupplierDetailsUpdateApiView.as_view(), name='supplier-update'),

    # customer detail
    path('customer/', CustomerListCreateApiView.as_view(), name='customer'),

    #company
    path('company/', CompanyListApiView.as_view(), name='company'),
    path('company-create/', CompanyListCreateApiView.as_view(), name='company'),
    path('company-update/', CompanyUpdateApiView.as_view(), name='company'),

    # Invoice
    path('invoices/', InvoicesListApiView.as_view(), name='invoices'),
    path('invoices-create/', InvoicesCreateApiView.as_view(), name='invoices-create'),
    path('credit-note/', InvoicesCreditNoteApiViews.as_view(), name='credit-note'),
    path('debit-note/', InvoicesDebitNoteApiView.as_view(), name='debit-note'),

    # Payment Method
    path('create-payment-order/', CreatePaypalOrder.as_view(), name='create-orders'),
    path('capture-payment-order/', CapturePaypalOrder.as_view(), name='capture-payment'),

    # Current Company Plan
    path('company-plan/', CompanyPlanRetrieveView.as_view(), name='company-plan-detail'),
    path('subscription-plan/', SubscriptionPlanListView.as_view(), name='subscription-plan-list'),
    path('payment-history/', PaymentHistoryListView.as_view(), name='payment-history-list'),

    # Dashboard
    path('request-summery/', DashboardApiView.as_view(), name='request-summery'),



]