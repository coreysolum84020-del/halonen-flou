import json
import requests
from flask import current_app

AUTHNET_API_URL = 'https://api.authorize.net/xml/v1/request.api'
HOSTED_PAYMENT_URL = 'https://accept.authorize.net/payment/payment'
SUCCESS_URL = 'https://web-production-f4c2c.up.railway.app/subscribe/success'
CANCEL_URL = 'https://web-production-f4c2c.up.railway.app/subscribe/cancel'

SERVICE_PRICES = {
    'lessons': 100.00,
    'production': 2500.00,
}


def create_hosted_payment(name, email, service_type, ref_id, custom_amount=None):
    """
    Creates an Authorize.net Accept Hosted payment page.

    Returns:
        str: URL to redirect the client to for payment.

    Raises:
        RuntimeError: if Authorize.net API returns an error result code.
    """
    login_id = current_app.config['AUTHNET_LOGIN_ID']
    transaction_key = current_app.config['AUTHNET_TRANSACTION_KEY']

    if service_type == 'promotion':
        amount = f'{float(custom_amount):.2f}'
    else:
        amount = f'{SERVICE_PRICES[service_type]:.2f}'

    payload = {
        'getHostedPaymentPageRequest': {
            'merchantAuthentication': {
                'name': login_id,
                'transactionKey': transaction_key,
            },
            'transactionRequest': {
                'transactionType': 'authCaptureTransaction',
                'amount': amount,
                'invoiceNum': ref_id,
                'customer': {'email': email},
                'billTo': {'firstName': name},
            },
            'hostedPaymentSettings': {
                'setting': [
                    {
                        'settingName': 'hostedPaymentReturnOptions',
                        'settingValue': json.dumps({
                            'url': SUCCESS_URL,
                            'cancelUrl': CANCEL_URL,
                            'showReceipt': True,
                        }),
                    },
                    {
                        'settingName': 'hostedPaymentButtonOptions',
                        'settingValue': json.dumps({'text': 'Pay Now'}),
                    },
                    {
                        'settingName': 'hostedPaymentCustomerOptions',
                        'settingValue': json.dumps({
                            'showEmail': False,
                            'requiredEmail': False,
                        }),
                    },
                ],
            },
        }
    }

    resp = requests.post(AUTHNET_API_URL, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get('messages', {}).get('resultCode') != 'Ok':
        messages = data.get('messages', {}).get('message', [])
        raise RuntimeError(f'Authorize.net error: {messages}')

    token = data['token']
    return f'{HOSTED_PAYMENT_URL}?token={token}'


def handle_webhook(form_data):
    """
    Processes an Authorize.net Silent Post payload (form-encoded dict).
    Sets Subscriber.status = 'active' when x_response_code is '1' (approved).

    Returns:
        bool: True if a subscriber was updated, False otherwise.
    """
    from app.models import Subscriber
    from app.extensions import db

    response_code = form_data.get('x_response_code')
    ref_id = form_data.get('x_invoice_num')

    if response_code != '1' or not ref_id:
        return False

    sub = Subscriber.query.filter_by(provider_customer_id=ref_id).first()
    if sub is None or sub.status == 'active':
        return False

    sub.status = 'active'
    db.session.commit()
    return True
