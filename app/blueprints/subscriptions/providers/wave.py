import requests
from flask import current_app

WAVE_GQL_URL = 'https://gql.waveapps.com/graphql/public'

SERVICE_DESCRIPTIONS = {
    'promotion': 'Artist Promotion — Daily Subscription',
    'lessons': 'Music Lessons — 1-Hour Session',
    'production': 'Artist Production — Full Project',
}

SERVICE_PRICES = {
    'lessons': '100.00',
    'production': '2500.00',
}


def _gql(query, variables=None):
    token = current_app.config['WAVE_API_TOKEN']
    resp = requests.post(
        WAVE_GQL_URL,
        json={'query': query, 'variables': variables or {}},
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if 'errors' in data:
        raise RuntimeError(f"Wave API error: {data['errors']}")
    return data['data']


def create_invoice(name, email, service_type, custom_amount=None):
    """
    Creates a Wave customer and invoice for the given subscriber details.

    Returns:
        tuple: (invoice_id: str, checkout_url: str)

    Raises:
        RuntimeError: if Wave API returns input errors or HTTP errors.
    """
    business_id = current_app.config['WAVE_BUSINESS_ID']

    # Step 1: Create customer (Wave returns existing if email matches)
    customer_data = _gql(
        """
        mutation CreateCustomer($businessId: ID!, $input: CustomerCreateInput!) {
            customerCreate(businessId: $businessId, input: $input) {
                customer { id }
                inputErrors { message path code }
            }
        }
        """,
        {'businessId': business_id, 'input': {'name': name, 'email': email}},
    )
    errs = customer_data['customerCreate']['inputErrors']
    if errs:
        raise RuntimeError(f"Wave customer error: {errs}")
    customer_id = customer_data['customerCreate']['customer']['id']

    # Step 2: Determine unit price
    if service_type == 'promotion':
        unit_price = f'{float(custom_amount):.2f}'
    else:
        unit_price = SERVICE_PRICES[service_type]

    # Step 3: Create invoice
    invoice_data = _gql(
        """
        mutation CreateInvoice($businessId: ID!, $input: InvoiceCreateInput!) {
            invoiceCreate(businessId: $businessId, input: $input) {
                invoice { id viewUrl }
                inputErrors { message path code }
            }
        }
        """,
        {
            'businessId': business_id,
            'input': {
                'customerId': customer_id,
                'items': [{
                    'description': SERVICE_DESCRIPTIONS[service_type],
                    'quantity': '1',
                    'unitPrice': unit_price,
                }],
            },
        },
    )
    errs = invoice_data['invoiceCreate']['inputErrors']
    if errs:
        raise RuntimeError(f"Wave invoice error: {errs}")

    invoice = invoice_data['invoiceCreate']['invoice']
    return invoice['id'], invoice['viewUrl']


def handle_webhook(payload):
    """
    Processes a Wave webhook payload.
    Sets Subscriber.status = 'active' when the invoice status is PAID.

    Returns:
        bool: True if a subscriber was updated, False otherwise.
    """
    from app.models import Subscriber
    from app.extensions import db

    try:
        invoice_data = payload.get('data', {}).get('invoice', {})
        invoice_id = invoice_data.get('id')
        status = invoice_data.get('status')
    except AttributeError:
        return False

    if not invoice_id or status != 'PAID':
        return False

    sub = Subscriber.query.filter_by(wave_invoice_id=invoice_id).first()
    if sub is None or sub.status == 'active':
        return False

    sub.status = 'active'
    db.session.commit()
    return True
