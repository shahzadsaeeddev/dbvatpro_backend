from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey

from api.models import Company, Invoice

from api.production.serializer import InvoiceProductionCreateSerializer, InvoiceProductionCreditNoteSerializer, \
    InvoiceProductionDebitNoteSerializer


class InvoicesProductionApiView(generics.CreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceProductionCreateSerializer
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



class InvoicesProductionCreditNoteApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceProductionCreditNoteSerializer

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



class InvoicesProductionDebitNoteApiView(generics.ListCreateAPIView):
    permission_classes = [HasAPIKey | IsAuthenticated]
    serializer_class = InvoiceProductionDebitNoteSerializer

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
























