import requests
from flask import current_app

WAVE_GQL_URL = 'https://gql.waveapps.com/graphql/public'

SERVICE_DESCRIPTIONS = {
    'promotion': 'Artist Promotion — Daily Subscription',
    'lessons': 'Music Lessons — 1-Hour Session',
    'production': 'Artist Production — Full Project',
}

# Wave product IDs (created once in Wave dashboard / via API)
SERVICE_PRODUCT_IDS = {
    'promotion': 'QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFiO1Byb2R1Y3Q6MTMyNzI1NjM1',
    'lessons':   'QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFiO1Byb2R1Y3Q6MTMyNzI1NjM2',
    'production':'QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFiO1Byb2R1Y3Q6MTMyNzI1NjM3',
}

SERVICE_PRICES = {
    'lessons': 100.00,
    'production': 2500.00,
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

    # Step 1: Create customer (businessId inside input per current Wave API)
    customer_data = _gql(
        """
        mutation CreateCustomer($input: CustomerCreateInput!) {
            customerCreate(input: $input) {
                customer { id }
                inputErrors { message path code }
            }
        }
        """,
        {'input': {'businessId': business_id, 'name': name, 'email': email}},
    )
    errs = customer_data['customerCreate']['inputErrors']
    if errs:
        raise RuntimeError(f"Wave customer error: {errs}")
    customer_id = customer_data['customerCreate']['customer']['id']

    # Step 2: Determine unit price
    if service_type == 'promotion':
        unit_price = float(custom_amount)
    else:
        unit_price = SERVICE_PRICES[service_type]

    # Step 3: Create invoice (businessId inside input, productId required per current Wave API)
    invoice_data = _gql(
        """
        mutation CreateInvoice($input: InvoiceCreateInput!) {
            invoiceCreate(input: $input) {
                invoice { id viewUrl }
                inputErrors { message path code }
            }
        }
        """,
        {
            'input': {
                'businessId': business_id,
                'customerId': customer_id,
                'items': [{
                    'productId': SERVICE_PRODUCT_IDS[service_type],
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
    invoice_id = invoice['id']

    # Step 4: Approve the invoice so the payment form appears on the hosted page
    _gql(
        """
        mutation ApproveInvoice($input: InvoiceApproveInput!) {
            invoiceApprove(input: $input) {
                didSucceed
                inputErrors { message }
            }
        }
        """,
        {'input': {'invoiceId': invoice_id}},
    )

    return invoice_id, invoice['viewUrl']


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
