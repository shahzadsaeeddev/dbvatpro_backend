import json

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from .xmlfiles.compliance import compliance_xml
from .zatca_operations.zatca import Zatca
import logging
from .models import Production, SupplierDetails

logger = logging.getLogger(__name__)

@shared_task
def process_otp_and_generate_x509(production_id, supplier_id, otp):
    try:
        logger.info(f"Starting OTP processing for Production ID: {production_id}")
        zatca = Zatca(production_id, otp=otp)

        result_data = zatca.generate_csid()
        if not result_data or result_data.status_code != 200:
            logger.error(f"CSID generation failed for Production ID {production_id}")
            return

        result = compliance_xml(supplier_id, production_id)
        if result == 200:
            x509_response = zatca.generate_x509()
            if x509_response:
                logger.info(f"X509 generation successful for Production ID: {production_id}")
            else:
                logger.error(f"X509 generation failed for Production ID: {production_id}")

    except Exception as e:
        logger.exception(f"Unexpected error in process_otp_and_generate_x509 task: {str(e)}")


