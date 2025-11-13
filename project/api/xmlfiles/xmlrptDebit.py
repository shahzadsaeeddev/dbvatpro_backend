from base64 import b64encode
from datetime import datetime
from ..statics.statics import INVOICE_CODES


def debitNote(**data):
    current_time = datetime.now().strftime("%H:%M:%S")
    invoice_lines = ''
    total_tax = 0
    total_line_amount = 0
    total_discount_amount = 0
    for s in data['invoice']['invoice_lines']:
        line_amount = round(float(s['price']) * float(s['quantity']), 3)
        tax = round(line_amount * .15, 3)
        total_tax +=  tax
        total_line_amount += line_amount
        total_discount_amount = + float(s['discount'])
        invoice_lines += """<cac:InvoiceLine>
                <cbc:ID>1</cbc:ID>
                <cbc:InvoicedQuantity unitCode="PCE">""" + s['quantity'] + """</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID="SAR">""" + str(line_amount) + """</cbc:LineExtensionAmount>
                <cac:TaxTotal>
                    <cbc:TaxAmount currencyID="SAR">""" + str(tax) + """</cbc:TaxAmount>
                    <cbc:RoundingAmount currencyID="SAR">""" + str(tax + line_amount) + """</cbc:RoundingAmount>

                </cac:TaxTotal>
                <cac:Item>
                    <cbc:Name>""" + s['name'] + """</cbc:Name>
                    <cac:ClassifiedTaxCategory>
                        <cbc:ID>S</cbc:ID>
                        <cbc:Percent>15</cbc:Percent>
                        <cac:TaxScheme>
                            <cbc:ID>VAT</cbc:ID>
                        </cac:TaxScheme>
                    </cac:ClassifiedTaxCategory>
                </cac:Item>
                <cac:Price>
                    <cbc:PriceAmount currencyID="SAR">""" + s['price'] + """</cbc:PriceAmount>
                    <cac:AllowanceCharge>
                        <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                        <cbc:AllowanceChargeReason>discount</cbc:AllowanceChargeReason>
                        <cbc:Amount currencyID="SAR">""" + s['discount'] + """</cbc:Amount>
                    </cac:AllowanceCharge>
                </cac:Price>
            </cac:InvoiceLine>"""
    
    
    xml="""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
<ext:UBLExtensions>
   
</ext:UBLExtensions>
    
    <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
    <cbc:ID>""" + data['invoice']['invoice_number'] + """</cbc:ID>
    <cbc:UUID>""" + str(data['invoice_uuid']) + """</cbc:UUID>
    <cbc:IssueDate>""" + str(data['invoice']['date']) + """</cbc:IssueDate>
    <cbc:IssueTime>""" + str(current_time) + """</cbc:IssueTime>
        """ + INVOICE_CODES[data['invoice']['document_types']] + """
    <cbc:Note languageID="ar">ABC</cbc:Note>
    <cbc:DocumentCurrencyCode>SAR</cbc:DocumentCurrencyCode>
    <cbc:TaxCurrencyCode>SAR</cbc:TaxCurrencyCode>
    <cac:BillingReference>
        <cac:InvoiceDocumentReference>
            <cbc:ID>?Invoice Number:""" + data['invoice']['invoice_number'] + """ ; Invoice Issue Date: 2021-02-10?</cbc:ID>
        </cac:InvoiceDocumentReference>
    </cac:BillingReference>
    <cac:AdditionalDocumentReference>
        <cbc:ID>ICV</cbc:ID>
        <cbc:UUID>""" + str(data['count']) + """</cbc:UUID>
    </cac:AdditionalDocumentReference>
    <cac:AdditionalDocumentReference>
        <cbc:ID>PIH</cbc:ID>
        <cac:Attachment>
            <cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">""" + data['invoice_pih'] + """</cbc:EmbeddedDocumentBinaryObject>
        </cac:Attachment>
    </cac:AdditionalDocumentReference>
    
    <cac:AdditionalDocumentReference>
        <cbc:ID>QR</cbc:ID>
        <cac:Attachment>
            <cbc:EmbeddedDocumentBinaryObject mimeCode="text/plain">ARdBaG1lZCBNb2hhbWVkIEFMIEFobWFkeQIPMzAxMTIxOTcxNTAwMDAzAxQyMDIyLTAzLTEzVDE0OjQwOjQwWgQHMTEwOC45MAUFMTQ0LjkGLFFuVkVleFc0bld2NENhRTM5YS82NkpwL09YTy9ldkhROHBEbEc3d2VxLzQ9B2BNRVlDSVFDOUtlN3JVMEcrbHcxakJ0RFkxVW5HVktmSGgwUk9BZFJuNTU0cEVYTmJVQUloQVB6S2l3cFBTV0h5Q0svbjQwUUZ2bEFzR1dsUzZ0L2VSQWNmTUdXdWVZUE8IWDBWMBAGByqGSM49AgEGBSuBBAAKA0IABGGDDKDmhWAITDv7LXqLX2cmr6+qddUkpcLCvWs5rC2O29W/hS4ajAK4Qdnahym6MaijX75Cg3j4aao7ouYXJ9EJSDBGAiEA7mHT6yg85jtQGWp3M7tPT7Jk2+zsvVHGs3bU5Z7YE68CIQD60ebQamYjYvdebnFjNfx4X4dop7LsEBFCNSsLY0IFaQ==</cbc:EmbeddedDocumentBinaryObject>
        </cac:Attachment>
</cac:AdditionalDocumentReference><cac:Signature>
      <cbc:ID>urn:oasis:names:specification:ubl:signature:Invoice</cbc:ID>
      <cbc:SignatureMethod>urn:oasis:names:specification:ubl:dsig:enveloped:xades</cbc:SignatureMethod>
</cac:Signature>
  """ + data['supplier'] + """
  """ + data['customer'] + """
    <cac:Delivery>
        <cbc:ActualDeliveryDate>""" + str(data['invoice']['date']) + """</cbc:ActualDeliveryDate>
        <cbc:LatestDeliveryDate>""" + str(data['invoice']['date']) + """</cbc:LatestDeliveryDate>
    </cac:Delivery>
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>""" + data['invoice']['payment_method'] + """</cbc:PaymentMeansCode>
        <cbc:InstructionNote>""" + data['invoice']['reason'] + """</cbc:InstructionNote>
    </cac:PaymentMeans>
    <cac:AllowanceCharge>
        <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
        <cbc:AllowanceChargeReason>discount</cbc:AllowanceChargeReason>
        <cbc:Amount currencyID="SAR">""" + str(total_discount_amount) + """</cbc:Amount>
        <cac:TaxCategory>
            <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5305">S</cbc:ID>
            <cbc:Percent>15</cbc:Percent>
            <cac:TaxScheme>
                <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5153">VAT</cbc:ID>
            </cac:TaxScheme>
        </cac:TaxCategory>
    </cac:AllowanceCharge>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="SAR">""" + str(total_tax) + """</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="SAR">""" + str(total_line_amount) + """</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="SAR">""" + str(total_tax) + """</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5305">S</cbc:ID>
                <cbc:Percent>15</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID schemeAgencyID="6" schemeID="UN/ECE 5153">VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="SAR">""" + str(total_tax) + """</cbc:TaxAmount>

    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="SAR">""" + str(total_line_amount) + """</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="SAR">""" + str(total_line_amount-total_discount_amount) + """</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="SAR">""" + str(total_line_amount+total_tax) + """</cbc:TaxInclusiveAmount>
        <cbc:AllowanceTotalAmount currencyID="SAR">""" + str(total_discount_amount) + """</cbc:AllowanceTotalAmount>
        <cbc:PrepaidAmount currencyID="SAR">0</cbc:PrepaidAmount>
        <cbc:PayableAmount currencyID="SAR">""" + str(total_line_amount-total_discount_amount+total_tax) + """</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>"""
    xml += invoice_lines
    xml+="""</Invoice>"""

    return b64encode(bytes(xml,'utf-8')).decode('utf-8')