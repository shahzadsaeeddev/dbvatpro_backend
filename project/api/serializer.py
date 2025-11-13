import base64
import json
from datetime import timedelta, date, datetime

from django.db import transaction
from rest_framework import serializers

from .csr.csid_create import generate_csid, generate_x509
from .csr.csr_generator import create_csr
from .models import *

from .sign_document.sign_service import sign_xml_document
from .xmlfiles.compliance import compliance_xml
from .xmlfiles.xmlrpt import invoices
from .xmlfiles.xmlrptCredit import creditNote
from .xmlfiles.xmlrptDebit import debitNote
from .zatca.clearance import ZatcaClearance
from .zatca.reporting import ZatcaReporting
from .zatca_operations.zatca import Zatca
from .task import process_otp_and_generate_x509
import logging

from accounts.keycloak import update_role_self
from accounts.models import Users

logger = logging.getLogger(__name__)


class LocationSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='seller_name', read_only=True)
    otp = serializers.CharField(write_only=True, required=False, max_length=6)
    x509 = serializers.CharField(write_only=True, required=False, max_length=6)

    # def get_production(self, instance):
    #     return {
    #         "csr": bool(instance.production.csr),
    #         "csid": bool(instance.production.csid),
    #         "x509": bool(instance.production.x509_certificate)
    #     }

    class Meta:
        model = EgsLocations
        exclude = ['branch', 'seller_name', 'tax_no', 'common_name', "schemeType", "schemeNo", "StreetName", "BuildingNumber", "PlotIdentification", "CitySubdivisionName", "CityName", "PostalZone"]
        # extra_kwargs = {'authentication_token': {'read_only': True}}

    def update(self, instance, validated_data):



        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if validated_data['enable_zatca']:
            zatca = Zatca(instance.id)
            csr_response = zatca.generate_csr()
            # if csr_response:
            #     Sandbox.objects.get_or_create(
            #         location=instance,
            #         defaults={
            #             'csr': csr_response.get('csr'),
            #             'private_key': csr_response.get('pvt'),
            #             'public_key': csr_response.get('pbl'),
            #             'csid': None,
            #             'csid_base64': None,
            #             'secret_csid': None,
            #             'csid_request': None,
            #             'x509_base64': None,
            #             'x509_certificate': None,
            #             'x509_secret': None,
            #             'x509_request': None,
            #         }
            #     )





        instance.save()
        return instance

    def create(self, validated_data):
        location = EgsLocations.objects.create(**validated_data)
        if location.enable_zatca:
            zatca = Zatca(location.id)
            csr_response = zatca.generate_csr()

        return location


class BusinessLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EgsLocations
        fields = ["schemeType", "schemeNo", "StreetName", "BuildingNumber", "PlotIdentification", "CitySubdivisionName", "CityName", "PostalZone", "TaxScheme"]

class LocationListSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='seller_name', read_only=True)
    class Meta:
        model = EgsLocations
        exclude = ['seller_name', 'tax_no', 'common_name']

class CSIDSeliazer(serializers.Serializer):
    scope = serializers.CharField(max_length=250)
    otp = serializers.IntegerField()


class ProductionSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(max_length=6, required=True, write_only=True)

    class Meta:
        model = Production
        fields = ['otp']

    def update(self, instance, validated_data):
        result = generate_csid(instance.csr, validated_data['otp'], 'production')
        if result.status_code != 200:
            raise serializers.ValidationError(result.text)
        result = json.loads(result.text)
        instance.csid = result['binarySecurityToken']
        instance.csid_base64 = base64.b64decode(bytes(result['binarySecurityToken'], 'utf-8')).decode('utf-8')
        instance.secret_csid = result['secret']
        instance.csid_request = result['requestID']
        instance.save()
        return instance


class ProductionX509Serializer(serializers.ModelSerializer):
    otp = serializers.CharField(max_length=6, required=True, write_only=True)

    class Meta:
        model = Production
        fields = ['otp']

    def update(self, instance, validated_data):
        result = generate_x509(instance.csid, instance.secret_csid, instance.csid_request, 'production')
        if result.status_code != 200:
            raise serializers.ValidationError(result.text)
        result = json.loads(result.text)
        instance.x509_base64 = base64.b64decode(bytes(result['data']['binarySecurityToken'], 'utf-8')).decode('utf-8')
        instance.x509_certificate = result['binarySecurityToken']
        instance.x509_secret = result['secret']
        instance.x509_request = result['requestID']
        instance.save()
        return instance


class ComplainceSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(max_length=6, required=True, write_only=True)

    class Meta:
        model = Production
        fields = ['otp']

    def update(self, instance, validated_data):
        result = generate_x509(instance.csid, instance.secret_csid, instance.csid_request, 'production')
        if result.status_code != 200:
            raise serializers.ValidationError(result.text)
        result = json.loads(result.text)
        instance.x509_base64 = base64.b64encode(bytes(result['binarySecurityToken'], 'utf-8')).decode('utf-8')
        instance.x509_certificate = result['binarySecurityToken']
        instance.x509_secret = result['secret']
        instance.x509_request = result['requestID']
        instance.save()
        return instance



class BusinessLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EgsLocations
        exclude = ['updated_at']




class BusinessLocationsUpdateSerializer(serializers.ModelSerializer):
    # otp = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = EgsLocations
        exclude = ['updated_at']

    # def update(self, instance, validated_data):
    #     otp = validated_data.pop('otp')
    #
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)
    #     zatca = Zatca(instance.id, otp)
    #     csr_response = create_csr(OU=instance.organisation_unit, O=instance.organisation, CN=instance.common_name, SN=instance.serial_number, UID=instance.tax_no, title=instance.title,
    #         registeredAddress=instance.registered_address,
    #         business=instance.business_category,
    #         TYPE='TSTZATCA-Code-Signing'
    #     )
    #
    #     if csr_response:
    #         production, created = Production.objects.get_or_create(company=instance.company)
    #         production.csr = csr_response.get('csr')
    #         production.private_key = csr_response.get('pvt')
    #         production.public_key = csr_response.get('pbl')
    #         production.save()
    #         if otp:
    #             zatca = Zatca(production.id, otp=otp)
    #
    #             result_data = zatca.generate_csid()
    #             if not result_data or result_data.status_code != 200:
    #                 logger.error(f"CSID generation failed for Production ID {production.id}")
    #                 return
    #             supplier = instance.company.supplier
    #             if supplier:
    #                 result = compliance_xml(supplier.xml_text, production.id)
    #                 if result == 200:
    #                     x509_response = zatca.generate_x509()
    #                     if x509_response:
    #                         logger.info(f"X509 generation successful for Production ID: {production.id}")
    #                     else:
    #                         logger.error(f"X509 generation failed for Production ID: {production.id}")
    #             else:
    #                 logger.error(f"No supplier found for company {instance.company.id}")
    #     instance.save()
    #     return instance





class SupplierEgsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDetails
        exclude = ['updated_at', 'xml_text']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDetail
        exclude = ['updated_at', 'company', 'xml_text']



class CompanySerializer(serializers.ModelSerializer):
    has_csid = serializers.SerializerMethodField()
    has_x509 = serializers.SerializerMethodField()
    is_simplified_invoice = serializers.SerializerMethodField()
    is_simplified_debit_note = serializers.SerializerMethodField()
    is_simplified_credit_note = serializers.SerializerMethodField()
    is_standard_invoice = serializers.SerializerMethodField()
    is_standard_debit_note = serializers.SerializerMethodField()
    is_standard_credit_note = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'api_key', 'secret_key', 'has_csid', 'has_x509',
            'is_simplified_invoice', 'is_simplified_debit_note', 'is_simplified_credit_note',
            'is_standard_invoice', 'is_standard_debit_note', 'is_standard_credit_note'
        ]

    def get_has_csid(self, obj):
        return bool(getattr(obj.production, 'csid', None))

    def get_has_x509(self, obj):
        return bool(getattr(obj.production, 'x509_certificate', None))

    def get_is_simplified_invoice(self, obj):
        return obj.production.is_simplified_invoice if hasattr(obj, 'production') else False

    def get_is_simplified_debit_note(self, obj):
        return obj.production.is_simplified_debit_note if hasattr(obj, 'production') else False

    def get_is_simplified_credit_note(self, obj):
        return obj.production.is_simplified_credit_note if hasattr(obj, 'production') else False

    def get_is_standard_invoice(self, obj):
        return obj.production.is_standard_invoice if hasattr(obj, 'production') else False

    def get_is_standard_debit_note(self, obj):
        return obj.production.is_standard_debit_note if hasattr(obj, 'production') else False

    def get_is_standard_credit_note(self, obj):
        return obj.production.is_standard_credit_note if hasattr(obj, 'production') else False





class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        exclude = ['updated_at', 'api_key', 'secret_key', 'expiry']



class CompanyCreateSerializer(serializers.ModelSerializer):
    csr = BusinessLocationsSerializer()
    supplier = SupplierEgsSerializer()

    class Meta:
        model = Company
        exclude = ['updated_at', 'api_key', 'secret_key', 'sandbox_secret_key']

    def create(self, validated_data):
        user = self.context['request'].user
        if user.company:
            raise serializers.ValidationError("You already have a company")

        csr_data = validated_data.pop('csr', None)
        supplier_data = validated_data.pop('supplier', None)

        with transaction.atomic():
            expiry_date = datetime.now().date() + timedelta(days=30)
            plan = SubscriptionPlan.objects.filter(default=True).first()
            company = Company.objects.create(**validated_data, plan=plan, expiry=expiry_date)

            company_name = (company.name[:3].upper())
            scheme_no = str(supplier_data.get("scheme_no"))
            tax_no = csr_data.get("tax_no")
            common_name = f"{company_name}-{scheme_no}-{tax_no}"

            if csr_data:
                serial_no = f"1-dbvatpro|2- version 2.0 |3-{uuid.uuid4()}"

                location = EgsLocations.objects.create(company=company, serial_number=serial_no,
                    common_name=common_name, organisation=company.name, **csr_data)

            if supplier_data:
                SupplierDetails.objects.create(company=company, city_subdivision_name=company.district, city_name=company.city, street_name=company.address, **supplier_data)

            user = self.context['request'].user
            Users.objects.filter(id=user.id).update(company=company)

            request = self.context.get('request')

            if request and hasattr(request, 'META'):
                auth_token = request.META.get('HTTP_AUTHORIZATION')
                auth_token = auth_token.split(' ')[1]
            else:
                auth_token = None

            update_role_self(auth_token, user.username)

            if location:
                csr_sandbox_response = create_csr(OU=location.organisation_unit, O=location.organisation, CN=location.common_name,
                    SN=location.serial_number, UID=location.tax_no, title=location.title, registeredAddress=location.registered_address,
                    business=location.business_category, TYPE='TSTZATCA-Code-Signing')


                csr_response = create_csr(OU=location.organisation_unit, O=location.organisation, CN=location.common_name, SN=location.serial_number,
                    UID=location.tax_no, title=location.title, registeredAddress=location.registered_address, business=location.business_category,
                    TYPE='ZATCA-Code-Signing')

                if csr_sandbox_response.get('status') != 200:
                    raise serializers.ValidationError("CSR generation failed")

                Sandbox.objects.create(company=company, csr=csr_sandbox_response.get('csr'), private_key=csr_sandbox_response.get('pvt'),
                    public_key=csr_sandbox_response.get('pbl'))


                Production.objects.create(company=company, csr=csr_response.get('csr'), private_key=csr_response.get('pvt'),
                    public_key=csr_response.get('pbl'),)

        return company




class InvoicesSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(write_only=True)
    invoice_lines = serializers.CharField(write_only=True)

    class Meta:
        model = Invoice
        exclude = ['updated_at', 'company']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'details', 'price']

class CompanyPlanSerializer(serializers.ModelSerializer):
    plan = SubscriptionSerializer()
    class Meta:
        model = Company
        fields = ['expiry', 'plan']


class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        exclude = ['id', 'updated_at']


class SubscriptionPlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'



class InvoiceLines(serializers.Serializer):
    name = serializers.CharField(write_only=True)
    price = serializers.CharField(write_only=True)
    discount = serializers.CharField(write_only=True)
    quantity = serializers.CharField(write_only=True)
    tax = serializers.CharField(write_only=True)


class InvoiceCreateSerializer(serializers.ModelSerializer):
    invoice_lines=InvoiceLines(many=True)
    class Meta:
        model = Invoice
        exclude = ['updated_at','company']
        extra_kwargs = {'hash':{'read_only':True},'icv':{'read_only':True},'uuid':{'read_only':True},
                        'xml_string':{'read_only':True},'status_code':{'read_only':True},
                        'status_response':{'read_only':True}}
    def create(self, validated_data):

        if Invoice.objects.filter(company=validated_data['company'], invoice_number=validated_data['invoice_number']).exists():
            raise serializers.ValidationError({"error": "This invoice number already exists for this company."})


        if validated_data.get('company'):
            pih = Invoice.objects.filter(company=validated_data['company']).last()
            icv=Invoice.objects.filter(company=validated_data['company']).filter(document_types=validated_data['document_types']).count()
            invoice_uuid = uuid.uuid4()
            formate_icv = str(icv + 1).zfill(4)
            print(formate_icv)

            xml_string = {
                'count': formate_icv,
                'invoice_uuid': invoice_uuid,
                'customer': validated_data['customer'].xml_text,
                'supplier': validated_data['company'].supplier.xml_text,
                'payment_code': validated_data['payment_method'],
                'invoice': validated_data,
                'invoice_pih': (pih.hash if pih and pih.hash else "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="),
            }

            invoice_xml = invoices(**xml_string)
            # print("XML string data:", invoice_xml)

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].production.private_key,
                                              validated_data['company'].production.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            qrcode = signedInvoice['invoiceQRCode']
            invoice_hash = signedInvoice['invoiceHash']
            #
            if validated_data['document_types'] == "Standard_invoice":
                # standard
                stats = ZatcaClearance(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_invoice":
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data=Invoice.objects.create(**validated_data,icv=formate_icv, status_code=status, xml_string=signedInvoice['invoiceXml'],status_response=stats, hash=invoice_hash,
                                             uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data


        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceCreditNoteSerializer(serializers.ModelSerializer):
    invoice_lines = InvoiceLines(many=True)

    class Meta:
        model = Invoice
        exclude = ['updated_at', 'company']
        extra_kwargs = {'hash': {'read_only': True}, 'icv': {'read_only': True}, 'uuid': {'read_only': True},
                        'xml_string': {'read_only': True}, 'status_code': {'read_only': True},
                        'status_response': {'read_only': True}, "reason": {'required': True}}

    def create(self, validated_data):
        user = self.context['request'].user

        if Invoice.objects.filter(company=validated_data['company'],
                                  invoice_number=validated_data['invoice_number']).exists():
            raise serializers.ValidationError({"error": "This invoice number already exists for this company."})

        if validated_data.get('company'):
            pih = Invoice.objects.filter(company=validated_data['company']).last()

            icv = Invoice.objects.filter(company=validated_data['company']).filter(document_types=validated_data['document_types']).count()

            invoice_uuid = uuid.uuid4()
            formate_icv = str(icv + 1).zfill(4)

            xml_string = {
                'count': formate_icv,
                'invoice_uuid': invoice_uuid,
                'customer': validated_data['customer'].xml_text,
                'supplier': validated_data['company'].supplier.xml_text,
                'payment_code': validated_data['payment_method'],
                'invoice': validated_data,
                'invoice_pih': (
                    pih.hash if pih and pih.hash else "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="),
            }

            invoice_xml = creditNote(**xml_string)
            # print("XML string data:", invoice_xml)

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].production.private_key,
                                              validated_data['company'].production.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            invoice_hash = signedInvoice['invoiceHash']
            qrcode = signedInvoice['invoiceQRCode']
            #
            if validated_data['document_types'] == "Standard_credit_note":
                # standard
                stats = ZatcaClearance(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_credit_note" :
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceDebitNoteSerializer(serializers.ModelSerializer):
    invoice_lines = InvoiceLines(many=True)

    class Meta:
        model = Invoice
        exclude = ['updated_at', 'company']
        extra_kwargs = {'hash': {'read_only': True}, 'icv': {'read_only': True}, 'uuid': {'read_only': True},
                        'xml_string': {'read_only': True}, 'status_code': {'read_only': True},
                        'status_response': {'read_only': True}, "reason": {'required': True}}

    def create(self, validated_data):

        if Invoice.objects.filter(company=validated_data['company'],
                                  invoice_number=validated_data['invoice_number']).exists():
            raise serializers.ValidationError({"error": "This invoice number already exists for this company."})

        if validated_data.get('company'):
            pih = Invoice.objects.filter(company=validated_data['company']).last()
            icv = Invoice.objects.filter(company=validated_data['company']).filter(document_types=validated_data['document_types']).count()
            invoice_uuid = uuid.uuid4()
            formate_icv = str(icv + 1).zfill(4)

            xml_string = {
                'count': formate_icv,
                'invoice_uuid': invoice_uuid,
                'customer': validated_data['customer'].xml_text,
                'supplier': validated_data['company'].supplier.xml_text,
                'payment_code': validated_data['payment_method'],
                'invoice': validated_data,
                'invoice_pih': (
                    pih.hash if pih and pih.hash else "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="),
            }

            invoice_xml = debitNote(**xml_string)
            # print("XML string data:", invoice_xml)

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].production.private_key,
                                              validated_data['company'].production.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            invoice_hash = signedInvoice['invoiceHash']
            qrcode = signedInvoice['invoiceQRCode']
            #
            if validated_data['document_types'] == "Standard_debit_note":
                # standard
                stats = ZatcaClearance(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_debit_note" :
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')





