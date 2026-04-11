import json
import requests
from flask import current_app, url_for

AUTHNET_API_URL = 'https://api.authorize.net/xml/v1/request.api'
HOSTED_PAYMENT_URL = 'https://accept.authorize.net/payment/payment'

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
        price = SERVICE_PRICES.get(service_type)
        if price is None:
            raise RuntimeError(f'Unknown service_type: {service_type}')
        amount = f'{price:.2f}'

    success_url = url_for('subscriptions.success', _external=True)
    cancel_url = url_for('subscriptions.cancel', _external=True)

    payload = {
        'getHostedPaymentPageRequest': {
            'merchantAuthentication': {
                'name': login_id,
                'transactionKey': transaction_key,
            },
            'transactionRequest': {
                'transactionType': 'authCaptureTransaction',
                'amount': amount,
                'order': {'invoiceNumber': ref_id},
                'customer': {'email': email},
                'billTo': {'firstName': name},
            },
            'hostedPaymentSettings': {
                'setting': [
                    {
                        'settingName': 'hostedPaymentReturnOptions',
                        'settingValue': json.dumps({
                            'url': success_url,
                            'cancelUrl': cancel_url,
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
    resp.encoding = 'utf-8-sig'  # Authorize.net returns UTF-8 BOM
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
