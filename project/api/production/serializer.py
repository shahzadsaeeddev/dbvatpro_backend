import uuid

from rest_framework import serializers

from api.models import Invoice

from api.sign_document.sign_service import sign_xml_document
from api.xmlfiles.xmlrpt import invoices
from api.xmlfiles.xmlrptCredit import creditNote
from api.xmlfiles.xmlrptDebit import debitNote
from api.zatca.clearance import ZatcaClearance
from api.zatca.reporting import ZatcaReporting

from api.models import Production, Company
from api.zatca_operations.zatca import Zatca

from api.models import SupplierDetails
from api.xmlfiles.compliance import compliance_xml


class ProductionInvoiceLines(serializers.Serializer):
    name = serializers.CharField(write_only=True)
    price = serializers.CharField(write_only=True)
    discount = serializers.CharField(write_only=True)
    quantity = serializers.CharField(write_only=True)
    tax = serializers.CharField(write_only=True)




class InvoiceProductionCreateSerializer(serializers.ModelSerializer):
    invoice_lines=ProductionInvoiceLines(many=True)
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
                                       "production")
                print(stats)
                status = stats['clearanceStatus']


            elif validated_data['document_types'] == "Simplified_invoice":
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "production")
                status = stats['reportingStatus']

            data=Invoice.objects.create(**validated_data,icv=formate_icv, status_code=status, xml_string=signedInvoice['invoiceXml'],status_response=stats, hash=invoice_hash,
                                             uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data


        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceProductionCreditNoteSerializer(serializers.ModelSerializer):
    invoice_lines = ProductionInvoiceLines(many=True)

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
                                       "production")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_credit_note" :
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "production")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class InvoiceProductionDebitNoteSerializer(serializers.ModelSerializer):
    invoice_lines = ProductionInvoiceLines(many=True)

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
                                       "production")
                status = stats['clearanceStatus']

            elif validated_data['document_types'] == "Simplified_debit_note" :
                # simplified
                stats = ZatcaReporting(validated_data['company'].production.x509_certificate,
                                       validated_data['company'].production.x509_secret, invoice_submit,
                                       "production")
                status = stats['reportingStatus']

            data = Invoice.objects.create(**validated_data, icv=formate_icv, status_code=status,
                                          xml_string=signedInvoice['invoiceXml'], status_response=stats,
                                          hash=invoice_hash,
                                          uuid=invoice_uuid, invoice_qrcode=qrcode)

            return data

        raise serializers.ValidationError('Company is required to create an invoice')


class ProductionCredentialSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Company
        fields = ['id', 'api_key', 'secret_key', 'otp']

    def validate(self, attrs):
        otp = attrs.get("otp")
        company = self.instance

        if not company:
            raise serializers.ValidationError("Company not found.")

        production = Production.objects.filter(company=company).first()
        if not production:
            raise serializers.ValidationError("Production credentials not found.")

        zatca = Zatca("production", production.id, otp)
        if not zatca.generate_csid():
            raise serializers.ValidationError("CSID generation failed.")

        supplier = SupplierDetails.objects.filter(company=company).first()
        result = compliance_xml(supplier.xml_text, production.id, scope='production')
        if result != 200:
            raise serializers.ValidationError("Compliance check failed.")

        if not zatca.generate_x509():
            raise serializers.ValidationError("X509 generation failed.")

        return attrs


# class ProductionCredentialSerializer(serializers.ModelSerializer):
#     otp = serializers.CharField(required=True, write_only=True)
#
#     class Meta:
#         model = Company
#         fields = ['id', 'api_key', 'secret_key', 'otp']
#
#     def validate(self, attrs):
#         otp = attrs.get("otp")
#         company = self.instance
#
#         if not company:
#             raise serializers.ValidationError("Company not found.")
#
#         production = Production.objects.filter(company=company).first()
#         if not production:
#             raise serializers.ValidationError("Production credentials not found.")
#
#         zatca = Zatca("production", production.id, otp)
#         if not zatca.generate_csid():
#             raise serializers.ValidationError("CSID generation failed.")
#
#         supplier = SupplierDetails.objects.filter(company=company).first()
#         result = compliance_xml(supplier.xml_text, production.id)
#         if result != 200:
#             raise serializers.ValidationError("Compliance check failed.")
#
#         if not zatca.generate_x509():
#             raise serializers.ValidationError("X509 generation failed.")
#
#         return attrs



