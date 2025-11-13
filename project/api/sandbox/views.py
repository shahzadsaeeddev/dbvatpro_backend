import logging
import uuid

from django.forms import model_to_dict
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from api.models import Company, Invoice
from api.sandbox.serializer import InvoiceSandboxSerializer, \
    InvoiceSandBoxCreditNoteSerializer, InvoiceSandboxDebitNoteSerializer, SandboxCredentialSerializer, \
    SandBoxViewSerializer, InvoiceResubmitSerializer

from api.production.serializer import ProductionCredentialSerializer

from api.models import SupplierDetails, Production, Sandbox
from api.xmlfiles.compliance import compliance_xml
from api.zatca_operations.zatca import Zatca

from api.sign_document.sign_service import sign_xml_document
from api.xmlfiles.xmlrpt import invoices
from api.zatca.clearance import ZatcaClearance
from api.zatca.reporting import ZatcaReporting

logger = logging.getLogger(__name__)


class InvoicesSandboxApiView(generics.CreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceSandboxSerializer
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


class ResubmitInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def post(self, request):
        company = None
        if request.user and request.user.is_authenticated:
            company = request.user.company
        else:
            api_key = request.headers.get("Authorization")
            if api_key and api_key.startswith("Api-Key "):
                key = api_key.split(" ")[1]
                try:
                    company = Company.objects.get(api_key=key)
                except Company.DoesNotExist:
                    raise PermissionDenied("Invalid API key. Company not found.")
            else:
                raise PermissionDenied("Authentication required.")

        serializer = InvoiceResubmitSerializer(data=request.data, context={"company": company})
        if serializer.is_valid():
            invoice = serializer.save()
            invoice_serialized = InvoiceSandboxSerializer(invoice)
            return Response({"message": "Invoice resubmitted successfully.", "invoice": invoice_serialized.data},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoicesSandboxCreditNoteApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceSandBoxCreditNoteSerializer

    def get_queryset(self):
        user = self.request.user
        api_key = self.request.headers.get("Authorization")

        if user and user.is_authenticated:
            return Invoice.objects.filter(company=user.company, )

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


class InvoicesSandboxDebitNoteApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceSandboxDebitNoteSerializer

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


class ValidateOtpApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        scope = request.data.get("scope")
        company = request.user.company

        if scope == "sandbox":
            serializer = SandboxCredentialSerializer(instance=company, data=request.data)
        elif scope == "production":
            serializer = ProductionCredentialSerializer(instance=company, data=request.data)
        else:
            return Response({"error": "Invalid scope"}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            return Response({"message": "CSID and X509 generated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ValidateSpecificActionApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        scope = request.data.get("scope")
        action = request.data.get("action")
        company = request.user.company

        data = Sandbox.objects.filter(company=company).first() if scope == "sandbox" else Production.objects.filter(
            company=company).first()

        if not data:
            return Response({"error": f"{scope.capitalize()} credentials not found."},
                            status=status.HTTP_400_BAD_REQUEST)

        zatca = Zatca(scope, data.id, request.data.get("otp"))
        response_data = {}

        if action == "csid":
            if not zatca.generate_csid():
                return Response({"error": "CSID generation failed."}, status=status.HTTP_400_BAD_REQUEST)
            response_data["message"] = "CSID generated successfully"

        elif action == "x509":
            if not zatca.generate_x509():
                return Response({"error": "X509 generation failed."}, status=status.HTTP_400_BAD_REQUEST)
            response_data["message"] = "X509 generated successfully"

        elif action == "compliance":
            supplier = SupplierDetails.objects.filter(company=company).first()
            if not supplier:
                return Response({"error": "Supplier details not found."}, status=status.HTTP_400_BAD_REQUEST)

            result_code = compliance_xml(supplier.xml_text, data.id)

            if result_code != 200:
                return Response({"error": "Compliance check failed."}, status=status.HTTP_400_BAD_REQUEST)

            response_data["message"] = "Compliance check passed"

        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)


class SandboxCredentialsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SandBoxViewSerializer

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
