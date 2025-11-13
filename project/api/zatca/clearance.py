import json

import requests
from requests.auth import HTTPBasicAuth

from ..statics.statics import CLEARANCE_URL


def ZatcaClearance(user, pas, data, typ):

    headers = {
        'Accept-Language': 'en',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Clearance-Status': '1',
        'Accept-Version': 'V2',

    }

    auth = HTTPBasicAuth(user, pas)

    response = requests.request("POST", CLEARANCE_URL[typ], auth=auth, headers=headers, data=json.dumps(data))
    return json.loads(response.text)
