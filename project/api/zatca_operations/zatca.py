import base64
import logging

from ..csr.csid_create import generate_csid, generate_x509
from ..models import Production, Sandbox

logger = logging.getLogger(__name__)


class Zatca:
    def __init__(self, scope, id, otp):
        self.id = id
        self.otp = otp
        self.scope = scope

    def generate_csid(self):
        try:
            record = Sandbox.objects.filter(pk=self.id).first() if self.scope == "sandbox" else Production.objects.filter(pk=self.id).first()
            if not record:
                logger.error(f"{self.scope.capitalize()} record not found with ID: {self.id}")
                return None

            csid_response = generate_csid(csr=record.csr, otp=self.otp, type=self.scope)
            if csid_response.status_code != 200:
                logger.error(f"Failed to generate CSID. Response: {csid_response.json()}")
                return None

            result = csid_response.json()
            record.csid = result['binarySecurityToken']
            record.csid_base64 = base64.b64decode(result['binarySecurityToken']).decode('utf-8')
            record.secret_csid = result['secret']
            record.csid_request = result['requestID']
            record.save()

            logger.info(f"CSID saved successfully for {self.scope.capitalize()} ID: {self.id}")
            return csid_response
        except Exception as e:
            logger.exception(f"Error generating CSID: {str(e)}")
            return None

    def generate_x509(self):
        try:
            record = Sandbox.objects.filter(id=self.id).first() if self.scope == "sandbox" else Production.objects.filter(id=self.id).first()
            if not record:
                logger.error(f"{self.scope.capitalize()} record not found with ID: {self.id}")
                return None

            x509_response = generate_x509(record.csid, record.secret_csid, record.csid_request, self.scope)
            if x509_response.status_code != 200:
                logger.error(f"X509 generation failed with status {x509_response.status_code}")
                return None

            result = x509_response.json()
            record.x509_base64 = base64.b64decode(result['binarySecurityToken']).decode('utf-8')
            record.x509_certificate = result['binarySecurityToken']
            record.x509_secret = result['secret']
            record.x509_request = result['requestID']
            record.save()

            logger.info(f"X509 certificate successfully generated for {self.scope.capitalize()} ID: {record.id}")
            return x509_response
        except Exception as e:
            logger.exception(f"Error generating X509: {str(e)}")
            return None