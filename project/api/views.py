from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from .apifilters import PaymentHistoryFilter, InvoiceFilter
from .paypal_sdk import get_paypal_access_token
from .serializer import *
from rest_framework import viewsets, permissions, generics, filters

from .task import *
from project import settings

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000



def Index(requests):
    return HttpResponse("Invalid URL Parameter")


class LocationView(viewsets.ModelViewSet):
    queryset = EgsLocations.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['registered_address', 'organisation', 'organisation_unit']

    def perform_create(self, serializer):
        return serializer.save(company=self.request.user.company, seller_name=self.request.user.username,
                               tax_no=self.request.user,
                               common_name=self.request.user.username)

    def get_queryset(self):
        return EgsLocations.objects.filter(company=self.request.user.company)



class LocationListView(generics.ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    def get_queryset(self):
        return EgsLocations.objects.filter(company=self.request.user.company)


class BusinessLocationView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BusinessLocationSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return EgsLocations.objects.filter(company=self.request.user.company)


class GenerateCSID(APIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get(self, request, location, *args, **kwargs):
        results = CSIDSeliazer().data
        return Response(results)

    def patch(self, request, location, *args, **kwargs):
        c = self.request.user.company.filter(authentication_token=location).first()

        if c == None:
            return Response(
                {"status": "400", "Message": "Failed", "data": "account not found with current secret key"},
                status=400)
        if 'production' == request.data['scope']:
            slz = ProductionSerializer(c.production, data=request.data)
        if slz.is_valid():

            return Response(
                {"status": "200", "Message": "Success", "data": slz.data},
                status=200)
        else:
            return Response(
                {"status": "200", "Message": "Success", "data": slz.errors},
                status=400)


class ProductionView(generics.RetrieveUpdateAPIView):
    queryset = Production.objects.all()
    serializer_class = ProductionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'company'

    def get_object(self, queryset=None):
        company = self.kwargs.get('company')
        obj = Production.objects.get(company=company)
        return obj


class ProductionX509View(generics.RetrieveUpdateAPIView):
    queryset = Production.objects.all()
    serializer_class = ProductionX509Serializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'company'

    def get_object(self, queryset=None):
        company = self.kwargs.get('company')
        obj = Production.objects.get(company=company)
        return obj





class BusinessLocationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = BusinessLocationsSerializer

    def get_queryset(self):
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return EgsLocations.objects.filter(company=company)
            except Company.DoesNotExist:
                return EgsLocations.objects.none()
        else:
            user = self.request.user
            if user and user.is_authenticated:
                return EgsLocations.objects.filter(company=user.company)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(company=user.company_id)


class BusinessLocationUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = BusinessLocationsUpdateSerializer

    def get_object(self):
        user = self.request.user
        company = None

        api_key = self.request.headers.get('Authorization')
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key, company not found.")
        elif isinstance(user, AnonymousUser) or not hasattr(user, 'company'):
            raise PermissionDenied("No API key provided and user is not authenticated.")
        else:
            company = user.company
        location = EgsLocations.objects.filter(company=company).first()
        if not location:
            raise PermissionDenied("No Location details found for the company's company.")

        return location

    def perform_update(self, serializer):
        serializer.save()






# class OTPVerificationView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request, location_id):
#         # try:
#         location = EgsLocations.objects.get(company_id=location_id)
#
#         otp = request.data.get('otp')
#         if not otp:
#             return Response({"detail": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
#
#         zatca = Zatca(location.id)
#
#         # try:
#         production = Production.objects.filter(company=location.company).first()
#         if not production:
#             return Response({"detail": "Production record not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         result_data = zatca.generate_csid(otp=otp, **production.__dict__)
#         if not result_data or result_data.status_code != 200:
#             logger.error(f"CSID generation failed for location {location.id}")
#             return Response({"detail": "Failed to generate CSID"}, status=status.HTTP_400_BAD_REQUEST)
#
#         generate_credentials_task.delay(location.id, production.id)
#
#         return Response({"detail": "OTP validated, certificates generation successfully."},
#                             status=status.HTTP_200_OK)
#
#         # except Exception as e:
#         #     logger.exception(f"Error during CSID generation: {str(e)}")
#         #     return Response({"detail": f"Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class SupplierDetailsCreateApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = SupplierEgsSerializer

    def get_queryset(self):
        company = self.request.user.company
        return SupplierDetails.objects.filter(company=company)

    def perform_create(self, serializer):
        company_id = self.request.data.get("company")
        company = Company.objects.get(id=company_id)
        serializer.save(company=company)


class SupplierDetailsUpdateApiView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = SupplierEgsSerializer

    def get_object(self):
        user = self.request.user
        company = None

        api_key = self.request.headers.get('Authorization')
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key, company not found.")
        elif isinstance(user, AnonymousUser) or not hasattr(user, 'company'):
            raise PermissionDenied("No API key provided and user is not authenticated.")
        else:
            company = user.company
        supplier = SupplierDetails.objects.filter(company=company).first()
        if not supplier:
            raise PermissionDenied("No supplier details found for the company's company.")

        return supplier

    def perform_update(self, serializer):
        serializer.save()



class CustomerListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = CustomerSerializer
    pagination_class = StandardResultsSetPagination
    queryset = CustomerDetail.objects.all()
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    search_fields = ['street_name', 'building_number', 'city_subdivision_name', 'city_name', 'postal_zone', 'registered_name', 'vat_number']

    def get_queryset(self):
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return CustomerDetail.objects.filter(company=company)
            except Company.DoesNotExist:
                return CustomerDetail.objects.none()
        else:
            user = self.request.user
            if user and user.is_authenticated:
                return CustomerDetail.objects.filter(company=user.company)


    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            serializer.save(company=user.company)
            return
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                serializer.save(company=company)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key. Company not found.")
        else:
            raise PermissionDenied("Authentication required.")


class CompanyListApiView(generics.ListAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = CompanySerializer
    queryset = Company.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated and user.company:
            return Company.objects.filter(id=user.company.id)
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return Company.objects.filter(id=company.id)
            except Company.DoesNotExist:
                return Company.objects.none()

        return Company.objects.none()


class CompanyListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = CompanyCreateSerializer

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            return Company.objects.filter(users=user)
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            return Company.objects.filter(api_key=key)
        return Company.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)
        else:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)




class CompanyUpdateApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = CompanyUpdateSerializer

    def get_object(self):
        user = self.request.user
        company = None

        api_key = self.request.headers.get('Authorization')
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key, company not found.")
        elif isinstance(user, AnonymousUser) or not hasattr(user, 'company'):
            raise PermissionDenied("No API key provided and user is not authenticated.")
        else:
            company = user.company
        location = Company.objects.filter(id=company.id).first()
        if not location:
            raise PermissionDenied("No Company details found")

        return location

    def perform_update(self, serializer):
        serializer.save()


class InvoicesCreateApiView(generics.CreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceCreateSerializer
    queryset = Invoice.objects.all()


    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            serializer.save(company=user.company)
            return
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                serializer.save(company=company)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key. Company not found.")
        else:
            raise PermissionDenied("Authentication required.")



class InvoicesListApiView(generics.ListAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoicesSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = InvoiceFilter
    search_fields = ('invoice_number', 'status_code', 'payment_method')

    def get_queryset(self):
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return Invoice.objects.filter(company=company).order_by('-created_at')
            except Company.DoesNotExist:
                return Invoice.objects.none()
        else:
            user = self.request.user
            if user and user.is_authenticated:
                return Invoice.objects.filter(company=user.company).order_by('-created_at')



class InvoicesCreditNoteApiViews(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceCreditNoteSerializer

    def get_queryset(self):
        user = self.request.user
        api_key = self.request.headers.get("Authorization")

        if user and user.is_authenticated:
            return Invoice.objects.filter(company=user.company)

        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return Invoice.objects.filter(company=company)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key. Company not found.")

        raise PermissionDenied("Authentication required.")


    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            serializer.save(company=user.company)
            return
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                serializer.save(company=company)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key. Company not found.")
        else:
            raise PermissionDenied("Authentication required.")


class InvoicesDebitNoteApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceDebitNoteSerializer

    def get_queryset(self):
        user = self.request.user
        api_key = self.request.headers.get("Authorization")

        if user and user.is_authenticated:
            return Invoice.objects.filter(company=user.company)

        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return Invoice.objects.filter(company=company)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key. Company not found.")

        raise PermissionDenied("Authentication required.")

    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            serializer.save(company=user.company)
        else:
            api_key = self.request.headers.get("Authorization")
            if api_key and api_key.startswith("Api-Key "):
                key = api_key.split(" ")[1]
                try:
                    company = Company.objects.get(api_key=key)
                    serializer.save(company=company)
                except Company.DoesNotExist:
                    raise PermissionDenied("Invalid API key. Company not found.")
            else:
                raise PermissionDenied("Authentication required.")





class CreatePaypalOrder(APIView):
    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')

        if not plan_id:
            return Response({"error": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        chosen_plan = SubscriptionPlan.objects.filter(id=plan_id).first()

        if not chosen_plan:
            return Response({"error": "Invalid plan_id, no plan found"}, status=status.HTTP_400_BAD_REQUEST)

        price = chosen_plan.price * chosen_plan.duration
        access_token = get_paypal_access_token()
        url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": str(price)
                    }
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            company = self.request.user.company
            PaymentHistory.objects.create(company=company, payment_plan=chosen_plan, amount=price, orderID=response.json()['id'])
            return Response(response.json(), status=status.HTTP_201_CREATED)
        else:
            return Response({"error": response.text}, status=response.status_code)




class CapturePaypalOrder(APIView):
    def post(self, request, *args, **kwargs):
        try:
            order_id = request.data.get('orderID')
            if not order_id:
                return Response({"error": "orderID is required."}, status=status.HTTP_400_BAD_REQUEST)
            access_token = get_paypal_access_token()
            if not access_token:
                return Response({"error": "Failed to retrieve PayPal access token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            response = requests.post(url, headers=headers)

            if response.status_code == 201:
                company = self.request.user.location.company
                payment = PaymentHistory.objects.filter(company=company,orderID=request.data['orderID']).update( **request.data,status="success")
                if company.plan and company.plan.duration:
                    today = datetime.now()
                    new_expiry_date = today + relativedelta(months=company.plan.duration)
                    company.expiry = new_expiry_date
                    company.save()

                return Response(
                    {
                        "message": "Payment captured successfully and subscription updated.",
                        "payment_details": {
                            "orderID": payment.orderID,
                            "payerID": payment.payerID,
                            "paymentID": payment.paymentID,
                        },
                        "expiry_date": company.expiry,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"error": "Failed to capture PayPal order.", "details": response.text},
                    status=response.status_code,
                )

        except Exception as e:
            return Response({"error": "An unexpected error occurred.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CompanyPlanRetrieveView(generics.RetrieveAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = CompanyPlanSerializer

    def get_object(self):
        api_key = self.request.headers.get('Authorization')
        company = None

        if api_key and api_key.startswith('Api-Key '):
            key = api_key.split(' ')[1]
            try:
                company = Company.objects.get(api_key=key)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key, company not found.")
        elif self.request.user and self.request.user.is_authenticated:
            company = self.request.user.company
        else:
            raise PermissionDenied("Authentication required: Provide an API key or be authenticated.")

        return company


class SubscriptionPlanListView(generics.ListAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = SubscriptionPlanListSerializer
    queryset = SubscriptionPlan.objects.filter(default = False)

    def get_object(self):
        api_key = self.request.headers.get('Authorization')
        company = None

        if api_key and api_key.startswith('Api-Key '):
            key = api_key.split(' ')[1]
            try:
                company = Company.objects.get(api_key=key)
            except Company.DoesNotExist:
                raise PermissionDenied("Invalid API key, company not found.")
        elif self.request.user and self.request.user.is_authenticated:
            company = self.request.user.company
        else:
            raise PermissionDenied("Authentication required: Provide an API key or be authenticated.")

        return company




class PaymentHistoryListView(generics.ListAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = PaymentHistorySerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    pagination_class = StandardResultsSetPagination
    filterset_class = PaymentHistoryFilter
    search_fields = ['orderID']
    queryset = PaymentHistory.objects.all()

    def get_queryset(self):
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return PaymentHistory.objects.filter(company=company)
            except Company.DoesNotExist:
                return PaymentHistory.objects.none()
        else:
            user = self.request.user
            if user and user.is_authenticated:
                return PaymentHistory.objects.filter(company=user.company)


class DashboardApiView(APIView):
    permission_classes = [HasAPIKey | IsAuthenticated]

    def get_queryset(self):
        api_key = self.request.headers.get("Authorization")
        if api_key and api_key.startswith("Api-Key "):
            key = api_key.split(" ")[1]
            try:
                company = Company.objects.get(api_key=key)
                return Invoice.objects.filter(company=company)
            except Company.DoesNotExist:
                return Invoice.objects.none()
        return Invoice.objects.filter(company=self.request.user.company)

    def get(self, request, *args, **kwargs):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        document_types = request.query_params.get('document_types')

        queryset = self.get_queryset()

        if start_date and end_date:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )

        if document_types:
            document_types = document_types.split(",")
            queryset = queryset.filter(document_types__in=document_types)

        total_invoices = queryset.count()

        invoice_status_counts = queryset.values('status_code').annotate(count=models.Count('id'))
        status_counts = {entry['status_code']: entry['count'] for entry in invoice_status_counts}

        invoice_document_types = queryset.values('document_types').annotate(count=models.Count('id'))
        document_types_counts = {entry['document_types']: entry['count'] for entry in invoice_document_types}

        possible_statuses = ["REPORTED", "CLEARED", "NOT_REPORTED", "NOT_CLEARED"]
        possible_document_types = ["Standard_invoice", "Simplified_invoice", "Standard_credit_note",
                                   "Simplified_credit_note", "Standard_debit_note", "Simplified_debit_note"]

        for status in possible_statuses:
            status_counts.setdefault(status, 0)

        for doc_type in possible_document_types:
            document_types_counts.setdefault(doc_type, 0)

        return Response({
            "total_invoices": total_invoices,
            "invoice_status": status_counts,
            "document_types": document_types_counts,
        })






