import json
import os
import time
import base64
from datetime import datetime

from bs4 import BeautifulSoup
from api.sign_document.sign_service import sign_xml_document
from api.zatca.complience import ZatcaCompliance
from api.models import Production, Sandbox
import logging

logger = logging.getLogger(__name__)


def compliance_xml(supplier, production_id, scope='sandbox'):
    """Processes XML files, signs invoices, and updates the database based on compliance validation."""
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        xml_directory = os.path.join(current_directory, "xml")

        if not os.path.exists(xml_directory):
            logger.error(f"XML directory not found: {xml_directory}")
            return 400

        data = Sandbox.objects.filter(id=production_id).first() or Production.objects.filter(id=production_id).first()

        if not data:
            logger.error(f"No record found with ID: {production_id}")
            return 400

        xml_files = [file.name for file in os.scandir(xml_directory) if file.is_file()]
        logger.info(f"Found {len(xml_files)} XML files in {xml_directory}")

        invoice_types = {
            "Standard_Invoice.xml": "is_standard_invoice",
            "Standard_Credit_Note.xml": "is_standard_credit_note",
            "Standard_Debit_Note.xml": "is_standard_debit_note",
            "Simplified_Invoice.xml": "is_simplified_invoice",
            "Simplified_Credit_Note.xml": "is_simplified_credit_note",
            "Simplified_Debit_Note.xml": "is_simplified_debit_note"
        }
        now = datetime.now()
        issue_date = now.strftime("%Y-%m-%d")  # e.g. 2025-06-24
        issue_time = now.strftime("%H:%M:%S")  # e.g. 15:42:10

        for file_name in xml_files:
            print(file_name)
            file_path = os.path.join(xml_directory, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                xml_content = file.read()
            xml_content = xml_content.replace("dddd", issue_date)
            xml_content = xml_content.replace("tttt", issue_time)
            xml_content = xml_content.replace("@@@@", supplier)
            # print(xml_content)
            soup = BeautifulSoup(xml_content, "lxml-xml")
            uuid_tag = soup.find("cbc:UUID")

            if not uuid_tag:
                logger.warning(f"UUID not found in {file_name}")
                continue

            uuid = uuid_tag.text
            encoded_invoice = base64.b64encode(str(soup).encode("utf-8")).decode("utf-8")

            signed_invoice = sign_xml_document(encoded_invoice, data.private_key, data.csid_base64)
            invoice_payload = {
                "invoiceHash": signed_invoice.get('invoiceHash'),
                "uuid": uuid,
                "invoice": signed_invoice.get('invoiceXml')
            }

            stats = ZatcaCompliance(data.csid, data.secret_csid, invoice_payload, scope)
          #  print(stats)
            # print(stats)
            logger.info(f"Compliance check completed for ID: {stats}")
            if stats.get('validationResults', {}).get('status') == "PASS":
                invoice_field = invoice_types.get(file_name)
                if invoice_field:
                    setattr(data, invoice_field, True)
            time.sleep(1)

        data.save()
        logger.info(f"Compliance check completed for ID: {production_id}")
        return 200

    except Exception as e:
        logger.exception(f"Error in compliance_xml: {str(e)}")
        return 401

