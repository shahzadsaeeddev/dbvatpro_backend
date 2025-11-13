import requests
from django.conf import settings


def get_paypal_access_token():
    url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data,
                             auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET))

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get PayPal access token: {response.text}")