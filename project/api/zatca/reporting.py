import json

import requests
from requests.auth import HTTPBasicAuth

from ..statics.statics import REPORTING_URL


def ZatcaReporting(user, pas, data, typ):

    headers = {
        'Accept-Language': 'en',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Clearance-Status': '1',
        'Accept-Version': 'V2',

    }

    auth = HTTPBasicAuth(user, pas)

    response = requests.request("POST", REPORTING_URL[typ], auth=auth, headers=headers, data=json.dumps(data))
    return json.loads(response.text)

