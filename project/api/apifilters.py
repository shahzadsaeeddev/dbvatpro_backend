from django_filters import rest_framework as filters
from .models import PaymentHistory, Invoice


class PaymentHistoryFilter(filters.FilterSet):
    class Meta:
        model = PaymentHistory
        fields = ['orderID', 'paymentID', 'status', 'amount']



class InvoiceFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    end_date = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = Invoice
        fields = ['start_date', 'end_date', 'document_types']