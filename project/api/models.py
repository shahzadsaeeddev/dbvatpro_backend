import uuid
from email.policy import default

from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver

import secrets

from rest_framework_api_key.models import APIKey
from utility.modelMixins import TimeStampMixins, CompanyMixins


def generate_key():
    private_key = secrets.token_bytes(32)
    return private_key.hex()

class SubscriptionPlan(TimeStampMixins):
    name = models.CharField(max_length=100, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    sale_price = models.DecimalField(max_digits=7, decimal_places=2)
    duration = models.PositiveIntegerField(null=True, blank=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Company(TimeStampMixins):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True , blank=True, related_name="companies")
    name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    expiry = models.DateField(null=True, blank=True)
    api_key = models.CharField(max_length=100, null=True, blank=True)
    secret_key = models.CharField(max_length=100, null=True, blank=True)
    sandbox_secret_key = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            slug_base = f"{self.name}"
            api_key, key = APIKey.objects.create_key(name=slug_base, expiry_date=self.expiry)
            self.api_key = key

        if not self.secret_key:
            self.secret_key = generate_key()

        if not self.sandbox_secret_key:
            self.sandbox_secret_key = generate_key()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class EgsLocations(TimeStampMixins):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, blank=True, related_name="csr", null=True)
    tax_no = models.CharField(blank=True, max_length=16)
    common_name = models.CharField(null=True, blank=True, max_length=230)
    organisation = models.CharField(blank=True, max_length=230)
    organisation_unit = models.CharField(blank=True, max_length=230)
    serial_number = models.CharField(blank=True, max_length=230)
    choices = (('1000', 'B2B'), ('0100', 'B2C'), ('1100', 'Both'))
    title = models.CharField(blank=True, max_length=230, choices=choices)
    registered_address = models.CharField(blank=True, max_length=230)
    business_category = models.CharField(blank=True, max_length=230, null=True)

    def __str__(self):
        return f'{self.organisation}'


class SupplierDetails(TimeStampMixins):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, blank=True, related_name="supplier")
    # Invoice setup
    schemaList = (
        ('TIN', 'TIN'), ('GCC', 'GCC'), ('IQA', 'IQA'), ('PAS', 'PAS'), ('CRN', 'CRN'), ('MOM', 'MOM'), ('MLS', 'MLS'),
        ('700', '700'), ('SAG', 'SAG'), ('OTH', 'OTH'))
    scheme_type = models.CharField(max_length=50, verbose_name="Scheme ID", null=True, blank=True, choices=schemaList)
    scheme_no = models.BigIntegerField(verbose_name="Scheme Number", null=True, blank=True, )
    street_name = models.CharField(max_length=255, verbose_name="Street Name", blank=True, null=True)
    building_number = models.CharField(max_length=50, verbose_name="Building Number", blank=True, null=True)
    city_subdivision_name = models.CharField(max_length=255, verbose_name="City Subdivision Name", blank=True, null=True)
    city_name = models.CharField(max_length=255, verbose_name="City Name", blank=True, null=True)
    postal_zone = models.CharField(max_length=50, verbose_name="Postal Zone", blank=True, null=True)
    registered_name = models.CharField(max_length=50, verbose_name="Registered Name", blank=True, null=True)
    vat_number = models.CharField(max_length=50, verbose_name="vat number", blank=True, null=True)
    tax_scheme = models.CharField(max_length=50, verbose_name="Tax Type", blank=True, null=True)
    xml_text = models.TextField(verbose_name="XML Text", blank=True, null=True)

    def __str__(self):
        return f'{self.company.name}'


class Production(TimeStampMixins):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, blank=True, related_name="production")
    private_key = models.TextField(blank=True, max_length=1000)
    public_key = models.TextField(blank=True, max_length=1000)
    csr = models.TextField(blank=True, max_length=2500)
    csid = models.TextField(blank=True, max_length=3500, null=True)
    csid_base64 = models.TextField(blank=True, max_length=3500, null=True)
    secret_csid = models.TextField(blank=True, max_length=2500, null=True)
    csid_request = models.TextField(blank=True, max_length=100, null=True)
    x509_base64 = models.TextField(blank=True, max_length=3500, null=True)
    x509_certificate = models.TextField(blank=True, max_length=3500, null=True)
    x509_secret = models.TextField(blank=True, max_length=500, null=True)
    x509_request = models.TextField(blank=True, max_length=100, null=True)
    is_simplified_invoice = models.BooleanField(default=False, verbose_name="Is Simplified Invoice")
    is_simplified_debit_note = models.BooleanField(default=False, verbose_name="Is Simplified debit note")
    is_simplified_credit_note = models.BooleanField(default=False, verbose_name="Is Simplified credit note")
    is_standard_invoice = models.BooleanField(default=False, verbose_name="Is Standard Invoice")
    is_standard_debit_note = models.BooleanField(default=False, verbose_name="Is Standard debit note")
    is_standard_credit_note = models.BooleanField(default=False, verbose_name="Is Standard credit note")
    def __str__(self):
        return str(self.company.name)



class Sandbox(TimeStampMixins):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, blank=True, related_name="sandbox")
    private_key = models.TextField(blank=True, max_length=1000)
    public_key = models.TextField(blank=True, max_length=1000)
    csr = models.TextField(blank=True, max_length=2500)
    csid = models.TextField(blank=True, max_length=3500, null=True)
    csid_base64 = models.TextField(blank=True, max_length=3500, null=True)
    secret_csid = models.TextField(blank=True, max_length=2500, null=True)
    csid_request = models.TextField(blank=True, max_length=100, null=True)
    x509_base64 = models.TextField(blank=True, max_length=3500, null=True)
    x509_certificate = models.TextField(blank=True, max_length=3500, null=True)
    x509_secret = models.TextField(blank=True, max_length=500, null=True)
    x509_request = models.TextField(blank=True, max_length=100, null=True)
    is_simplified_invoice = models.BooleanField(default=False, verbose_name="Is Simplified Invoice")
    is_simplified_debit_note = models.BooleanField(default=False, verbose_name="Is Simplified debit note")
    is_simplified_credit_note = models.BooleanField(default=False, verbose_name="Is Simplified credit note")
    is_standard_invoice = models.BooleanField(default=False, verbose_name="Is Standard Invoice")
    is_standard_debit_note = models.BooleanField(default=False, verbose_name="Is Standard debit note")
    is_standard_credit_note = models.BooleanField(default=False, verbose_name="Is Standard credit note")
    def __str__(self):
        return f'{self.company.name}'




class CustomerDetail(CompanyMixins):
    street_name = models.CharField(max_length=255, verbose_name="Street Name", blank=True, null=True)
    building_number = models.CharField(max_length=50, verbose_name="Building Number", blank=True, null=True)
    city_subdivision_name = models.CharField(max_length=255, verbose_name="City Subdivision Name", blank=True, null=True)
    city_name = models.CharField(max_length=255, verbose_name="City Name", blank=True, null=True)
    postal_zone = models.CharField(max_length=50, verbose_name="Postal Zone", blank=True, null=True)
    registered_name = models.CharField(max_length=50, verbose_name="Registered Name", blank=True, null=True)
    vat_number = models.CharField(max_length=50, verbose_name="vat number", blank=True, null=True)
    tax_scheme = models.CharField(max_length=50, verbose_name="Tax Type", blank=True, null=True)
    xml_text = models.TextField(verbose_name="XML Text", blank=True, null=True)

    def __str__(self):
        return f'{self.registered_name}'


class Invoice(CompanyMixins):
    uuid = models.UUIDField(null=True, blank=True)
    invoice_number = models.CharField(max_length=255, verbose_name="Invoice Number", blank=True, null=True)
    hash = models.CharField(null=True, blank=True, max_length=500)
    date = models.DateField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    customer = models.ForeignKey(CustomerDetail, on_delete=models.CASCADE, related_name="invoice")
    choices = (
        ('10', 'Cash,نقدي'),
        ('30', 'Credit,ذمم'),
        ('42', 'Bank Transfer,حوالة بنكية'),
        ('48', 'Bank Card, Visa Mada'),
        ('1', 'Instrument not defined,اخرى')
    )
    payment_method = models.TextField(null=True, blank=True, choices=choices)
    icv = models.CharField(max_length=10, null=True, blank=True)
    invoice_typ = (
        ("Standard_invoice", "Standard Invoice"),
        ("Standard_credit_note", "Standard Credit Note"),
        ("Standard_debit_note", "Standard Debit Note"),
        ("Simplified_invoice", "Simplified Invoice"),
        ("Simplified_credit_note", "Simplified Credit Note"),
        ("Simplified_debit_note", "Simplified Debit Note"),
    )
    document_types = models.CharField(null=True, blank=True, max_length=500, choices=invoice_typ)
    invoice_lines = JSONField(null=True, blank=True)
    xml_string = models.TextField(null=True, blank=True)
    status_code = models.CharField(null=True, blank=True, max_length=500)
    status_response = models.TextField(null=True, blank=True, max_length=1500)
    invoice_qrcode = models.CharField(null=True, blank=True, max_length=1000)

    def __str__(self):
        return f'{self.invoice_number}'



class PaymentHistory(TimeStampMixins):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_history')
    payment_plan = models.ForeignKey(SubscriptionPlan, null=True,blank=True,on_delete=models.CASCADE)
    orderID = models.CharField(max_length=100, null=True, blank=True)
    payerID = models.CharField(max_length=100, null=True, blank=True)
    paymentID = models.CharField(max_length=100, null=True, blank=True)
    billingToken = models.CharField(max_length=100, blank=True, null=True)
    facilitatorAccessToken = models.CharField(max_length=200, blank=True, null=True)
    paymentSource = models.CharField(max_length=100, blank=True, null=True)
    amount= models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    status=(("pending","Pending"),("success","success"),("failed","failed"))
    status = models.CharField(max_length=100, null=True, blank=True,default="pending",choices=status)

    def __str__(self):
        return self.orderID




def xml_string(data):
    return """<cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID='""" + str(data.get('schemaType', '') or '') + """'>""" + str(
        data.get('schemaNo', '') or '') + """</cbc:ID>
            </cac:PartyIdentification>
            <cac:PostalAddress>
                <cbc:StreetName>""" + str(data.get('streetName') or '') + """</cbc:StreetName>
                <cbc:BuildingNumber>""" + str(data.get('buildingNumber') or '') + """</cbc:BuildingNumber>
                <cbc:PlotIdentification>""" + str(data.get('plotIdentification') or '') + """</cbc:PlotIdentification>
                <cbc:CitySubdivisionName>""" + str(data.get('citySubdivisionName') or '') + """</cbc:CitySubdivisionName>
                <cbc:CityName>""" + str(data.get('cityName') or '') + """</cbc:CityName>
                <cbc:PostalZone>""" + str(data.get('postalZone') or '') + """</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>SA</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>""" + str(data.get('companyID') or '') + """</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>""" + str(data.get('taxID') or '') + """</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>""" + str(data.get('registrationName') or '') + """</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>"""


# customer xml
def customer_xml(data):
    return """<cac:AccountingCustomerParty>
    <cac:Party>
        <cac:PostalAddress>
            <cbc:StreetName>""" + (data.get('streetName') or '') + """</cbc:StreetName>
            <cbc:BuildingNumber>""" + (data.get('buildingNumber') or '') + """</cbc:BuildingNumber>
            <cbc:CitySubdivisionName>""" + (data.get('citySubdivisionName') or '') + """</cbc:CitySubdivisionName>
            <cbc:CityName>""" + (data.get('cityName') or '') + """</cbc:CityName>
            <cbc:PostalZone>""" + (data.get('postalZone') or '') + """</cbc:PostalZone>
            <cac:Country>
                <cbc:IdentificationCode>SA</cbc:IdentificationCode>
            </cac:Country>
        </cac:PostalAddress>
        <cac:PartyTaxScheme>
            <cbc:CompanyID>""" + (data.get('companyID') or '') + """</cbc:CompanyID>
            <cac:TaxScheme>
                <cbc:ID>""" + (data.get('taxID') or '') + """</cbc:ID>
            </cac:TaxScheme>
        </cac:PartyTaxScheme>
        <cac:PartyLegalEntity>
            <cbc:RegistrationName>""" + (data.get('registrationName') or '') + """</cbc:RegistrationName>
        </cac:PartyLegalEntity>
    </cac:Party>
</cac:AccountingCustomerParty>"""



@receiver(post_save, sender=SupplierDetails, dispatch_uid="update_xml_text")
def update_xml_text_signal(sender, instance, created, **kwargs):
    xml_data = {
        'schemaType': instance.scheme_type, 'schemaNo': instance.scheme_no,
        'streetName': instance.scheme_no,
        'buildingNumber': instance.building_number,
        # 'plotIdentification': instance.plot_identification,
        'citySubdivisionName': instance.city_subdivision_name,
        'cityName': instance.city_name,
        'postalZone': instance.postal_zone,
        'companyID': instance.company.csr.tax_no,
        'taxID': instance.tax_scheme,
        'registrationName': instance.company.csr.organisation,
    }

    xml_result = xml_string(xml_data)

    if created or instance.xml_text != xml_result:
        instance.xml_text = xml_result
        instance.save()


@receiver(post_save, sender=CustomerDetail, dispatch_uid="updated_xml_text")
def update_xml_text_signal(sender, instance, created, **kwargs):
    xml_data = {
        'streetName': (instance.street_name or "صلاح الدين | Salah Al-Din"),
        'buildingNumber': (instance.building_number or "1111"),
        'citySubdivisionName': (instance.city_subdivision_name or "المروج | Al-Murooj"),
        'cityName': (instance.city_name or "الرياض | Riyadh"),
        'postalZone': (instance.postal_zone or "12222"),
        'companyID': (instance.vat_number or "399999999800003"),
        'taxID': (instance.tax_scheme or "VAT"),
        'registrationName': (instance.registered_name or "شركة نماذج فاتورة المحدودة | Fatoora Samples LTD"),
    }

    xml_result = customer_xml(xml_data)

    if created or instance.xml_text != xml_result:
        instance.xml_text = xml_result
        instance.save()
