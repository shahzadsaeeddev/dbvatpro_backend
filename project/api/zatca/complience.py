from requests.auth import HTTPBasicAuth

from ..statics.statics import COMPLIANCE_URL
import requests
import json
def ZatcaCompliance(user, pas, data, typ):
    headers = {
        'Accept-Language': 'en',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Version': 'V2',
    }
    auth = HTTPBasicAuth(user, pas)
    response = requests.request("POST", COMPLIANCE_URL[typ], auth=auth, headers=headers, data=json.dumps(data))
    return json.loads(response.text)

