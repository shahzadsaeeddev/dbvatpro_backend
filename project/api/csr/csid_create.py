import json

import requests
from requests.auth import HTTPBasicAuth

from ..statics.statics import CSID,X509

def generate_csid(csr, otp,type):
    payload = json.dumps({
        "csr": csr
    })
    headers = {
        'Content-Type':'application/json',
        'OTP': otp,
        'Accept-Version': 'V2',
        'accept': 'application/json'
    }
    response = requests.request("POST", CSID[type], headers=headers, data=payload)

    return response


def generate_x509(user, pas, req,type):
    auth = HTTPBasicAuth(user, pas)
    payload = json.dumps({
        "compliance_request_id": req
    })
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Accept-Version': 'V2',
    }
    response = requests.request("POST", X509[type], auth=auth, headers=headers, data=payload)

    return response