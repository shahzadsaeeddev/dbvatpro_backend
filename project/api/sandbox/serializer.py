import uuid

from django.forms import model_to_dict
from rest_framework import serializers

from api.models import Invoice, Company

from api.sign_document.sign_service import sign_xml_document
from api.xmlfiles.xmlrpt import invoices
from api.xmlfiles.xmlrptCredit import creditNote
from api.xmlfiles.xmlrptDebit import debitNote
from api.zatca.clearance import ZatcaClearance
from api.zatca.reporting import ZatcaReporting
from api.models import Sandbox
from api.zatca_operations.zatca import Zatca

from api.xmlfiles.compliance import compliance_xml

from api.models import SupplierDetails


class SandboxInvoiceLines(serializers.Serializer):
    name = serializers.CharField(write_only=True)
    price = serializers.CharField(write_only=True)
    discount = serializers.CharField(write_only=True)
    quantity = serializers.CharField(write_only=True)
    tax = serializers.CharField(write_only=True)


class InvoiceSandboxSerializer(serializers.ModelSerializer):
    invoice_lines = SandboxInvoiceLines(many=True)

    class Meta:
        model = Invoice
        exclude = ['updated_at', 'company']
        extra_kwargs = {'hash': {'read_only': True}, 'icv': {'read_only': True}, 'uuid': {'read_only': True},
                        'xml_string': {'read_only': True}, 'status_code': {'read_only': True},
                        'status_response': {'read_only': True}}

    def create(self, validated_data):

        if Invoice.objects.filter(company=validated_data['company'],
                                  invoice_number=validated_data['invoice_number']).exists():
            raise serializers.ValidationError({"error": "This invoice number already exists for this company."})

        if validated_data.get('company'):
            pih = Invoice.objects.filter(company=validated_data['company']).last()
            icv = Invoice.objects.filter(company=validated_data['company']).filter(
                document_types=validated_data['document_types']).count()
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
                'invoice_pih': (
                    pih.hash if pih and pih.hash else "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="),
            }

            invoice_xml = invoices(**xml_string)

            # print("XML string data:", invoice_xml)

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].sandbox.private_key,
                                              validated_data['company'].sandbox.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            qrcode = signedInvoice['invoiceQRCode']
            invoice_hash = signedInvoice['invoiceHash']
            #
            if validated_data['document_types'] == "Standard_invoice":
                # standard
                stats = ZatcaClearance(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_invoice":
                # simplified
                stats = ZatcaReporting(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceSandBoxCreditNoteSerializer(serializers.ModelSerializer):
    invoice_lines = SandboxInvoiceLines(many=True)

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

            icv = Invoice.objects.filter(company=validated_data['company']).filter(
                document_types=validated_data['document_types']).count()

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

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].sandbox.private_key,
                                              validated_data['company'].sandbox.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            invoice_hash = signedInvoice['invoiceHash']
            qrcode = signedInvoice['invoiceQRCode']
            #
            if validated_data['document_types'] == "Standard_credit_note":
                # standard
                stats = ZatcaClearance(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_credit_note":
                # simplified
                stats = ZatcaReporting(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceSandboxDebitNoteSerializer(serializers.ModelSerializer):
    invoice_lines = SandboxInvoiceLines(many=True)

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
            icv = Invoice.objects.filter(company=validated_data['company']).filter(
                document_types=validated_data['document_types']).count()
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

            signedInvoice = sign_xml_document(invoice_xml, validated_data['company'].sandbox.private_key,
                                              validated_data['company'].sandbox.x509_base64)

            invoice_submit = {"invoiceHash": signedInvoice['invoiceHash'],
                              "uuid": str(invoice_uuid), "invoice": signedInvoice['invoiceXml']}

            invoice_hash = signedInvoice['invoiceHash']
            qrcode = signedInvoice['invoiceQRCode']
            #
            if validated_data['document_types'] == "Standard_debit_note":
                # standard
                stats = ZatcaClearance(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_debit_note":
                # simplified
                stats = ZatcaReporting(validated_data['company'].sandbox.x509_certificate,
                                       validated_data['company'].sandbox.x509_secret, invoice_submit,
                                       "sandbox")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class SandboxCredentialSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Company
        fields = ['id', 'api_key', 'secret_key', 'otp']

    def validate(self, attrs):
        otp = attrs.get("otp")
        company = self.instance

        if not company:
            raise serializers.ValidationError("Company not found.")

        sandbox = Sandbox.objects.filter(company=company).first()
        if not sandbox:
            raise serializers.ValidationError("Sandbox credentials not found.")

        zatca = Zatca("sandbox", sandbox.id, otp)
        if not zatca.generate_csid():
            raise serializers.ValidationError("CSID generation failed.")

        supplier = SupplierDetails.objects.filter(company=company).first()
        result = compliance_xml(supplier.xml_text, sandbox.id, scope='sandbox')
        if result != 200:
            raise serializers.ValidationError("Compliance check failed.")

        if not zatca.generate_x509():
            raise serializers.ValidationError("X509 generation failed.")

        return attrs


# class SandboxCredentialSerializer(serializers.ModelSerializer):
#     otp = serializers.CharField(required=True, write_only=True)
#
#     class Meta:
#         model = Company
#         fields = ['id', 'api_key', 'sandbox_secret_key', 'otp']
#
#     def validate(self, attrs):
#         otp = attrs.get("otp")
#         company = self.instance
#
#         if not company:
#             raise serializers.ValidationError("Company not found.")
#
#         sandbox = Sandbox.objects.filter(company=company).first()
#         if not sandbox:
#             raise serializers.ValidationError("Sandbox credentials not found.")
#
#         zatca = Zatca("sandbox", sandbox.id, otp)
#         if not zatca.generate_csid():
#             raise serializers.ValidationError("CSID generation failed.")
#
#         supplier = SupplierDetails.objects.filter(company=company).first()
#         result = compliance_xml(supplier.xml_text, sandbox.id)
#         if result != 200:
#             raise serializers.ValidationError("Compliance check failed.")
#
#         if not zatca.generate_x509():
#             raise serializers.ValidationError("X509 generation failed.")
#
#         return attrs


class SandBoxViewSerializer(serializers.ModelSerializer):
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
            'api_key', 'sandbox_secret_key', 'has_csid', 'has_x509',
            'is_simplified_invoice', 'is_simplified_debit_note', 'is_simplified_credit_note',
            'is_standard_invoice', 'is_standard_debit_note', 'is_standard_credit_note'
        ]

    def get_has_csid(self, obj):
        return bool(getattr(obj.sandbox, 'csid', None))

    def get_has_x509(self, obj):
        return bool(getattr(obj.sandbox, 'x509_certificate', None))

    def get_is_simplified_invoice(self, obj):
        return obj.sandbox.is_simplified_invoice if hasattr(obj, 'sandbox') else False

    def get_is_simplified_debit_note(self, obj):
        return obj.sandbox.is_simplified_debit_note if hasattr(obj, 'sandbox') else False

    def get_is_simplified_credit_note(self, obj):
        return obj.sandbox.is_simplified_credit_note if hasattr(obj, 'sandbox') else False

    def get_is_standard_invoice(self, obj):
        return obj.sandbox.is_standard_invoice if hasattr(obj, 'sandbox') else False

    def get_is_standard_debit_note(self, obj):
        return obj.sandbox.is_standard_debit_note if hasattr(obj, 'sandbox') else False

    def get_is_standard_credit_note(self, obj):
        return obj.sandbox.is_standard_credit_note if hasattr(obj, 'sandbox') else False


class InvoiceResubmitSerializer(serializers.Serializer):
    invoice_id = serializers.UUIDField()

    def validate(self, data):
        company = self.context['company']
        try:
            invoice = Invoice.objects.get(id=data['invoice_id'], company=company)
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found.")
        data['invoice'] = invoice
        return data

    def save(self, **kwargs):
        invoice = self.validated_data['invoice']
        company = self.context['company']
        signed_invoice = sign_xml_document(invoice.xml_string, company.sandbox.private_key, company.sandbox.x509_base64)
        invoice_submit = {
            "invoiceHash": signed_invoice['invoiceHash'],
            "uuid": str(invoice.uuid),
            "invoice": signed_invoice['invoiceXml']
        }

        if "Standard" in invoice.document_types:
            response = ZatcaClearance(company.sandbox.x509_certificate, company.sandbox.x509_secret, invoice_submit,
                                      "sandbox")
            status_code = response.get("clearanceStatus")
        else:
            response = ZatcaReporting(company.sandbox.x509_certificate, company.sandbox.x509_secret, invoice_submit,
                                      "sandbox")
            status_code = response.get("reportingStatus")

        invoice.xml_string = signed_invoice['invoiceXml']
        invoice.hash = signed_invoice['invoiceHash']
        invoice.invoice_qrcode = signed_invoice['invoiceQRCode']
        invoice.status_code = status_code
        invoice.status_response = response
        invoice.save()

        return invoice
