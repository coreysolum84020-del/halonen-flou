import time
import uuid
import requests
from flask import current_app

QBP_CHARGES_URL = 'https://api.intuit.com/quickbooks/v4/payments/charges'
QBP_TOKEN_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'

SERVICE_PRICES = {
    'lessons': 100.00,
    'production': 2500.00,
}


def _save_config(key, value):
    from app.models import AppConfig
    from app.extensions import db
    row = db.session.get(AppConfig, key)
    if row:
        row.value = value
    else:
        db.session.add(AppConfig(key=key, value=value))


def get_access_token():
    """
    Returns a valid QBP access token, refreshing it if expired.

    Raises:
        RuntimeError: if no tokens exist in DB (OAuth not set up).
    """
    from app.models import AppConfig
    from app.extensions import db

    access_row = db.session.get(AppConfig, 'qbp_access_token')
    expiry_row = db.session.get(AppConfig, 'qbp_token_expiry')

    if not access_row or not access_row.value:
        raise RuntimeError('QuickBooks Payments not configured. Visit /setup/qbp to authorize.')

    if expiry_row and float(expiry_row.value) > time.time() + 60:
        return access_row.value

    # Access token expired — refresh it
    refresh_row = db.session.get(AppConfig, 'qbp_refresh_token')
    if not refresh_row or not refresh_row.value:
        raise RuntimeError('QuickBooks Payments not configured. Visit /setup/qbp to authorize.')

    client_id = current_app.config['QBP_CLIENT_ID']
    client_secret = current_app.config['QBP_CLIENT_SECRET']

    resp = requests.post(
        QBP_TOKEN_URL,
        data={'grant_type': 'refresh_token', 'refresh_token': refresh_row.value},
        auth=(client_id, client_secret),
        headers={'Accept': 'application/json'},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    _save_config('qbp_access_token', data['access_token'])
    _save_config('qbp_refresh_token', data['refresh_token'])
    _save_config('qbp_token_expiry', str(time.time() + data['expires_in']))
    db.session.commit()

    return data['access_token']


def charge_card(name, email, service_type, amount, card_number, exp_month, exp_year, cvc):
    """
    Charges a card via QuickBooks Payments API.

    Args:
        amount: float or None. Used only for 'promotion' service_type.

    Returns:
        str: charge ID on success.

    Raises:
        RuntimeError: if charge is declined, API returns error, or tokens missing.
    """
    if service_type == 'promotion':
        amt = float(amount) if amount is not None else 0.0
        if amt < 1.0:
            raise RuntimeError('Promotion amount must be at least $1.00')
        charge_amount = f'{amt:.2f}'
    else:
        price = SERVICE_PRICES.get(service_type)
        if price is None:
            raise RuntimeError(f'Unknown service_type: {service_type}')
        charge_amount = f'{price:.2f}'

    access_token = get_access_token()

    payload = {
        'amount': charge_amount,
        'currency': 'USD',
        'card': {
            'number': card_number,
            'expMonth': exp_month,
            'expYear': exp_year,
            'cvc': cvc,
            'name': name,
        },
        'capture': True,
        'context': {
            'mobile': False,
            'isEcommerce': True,
        },
    }

    resp = requests.post(
        QBP_CHARGES_URL,
        json=payload,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Request-Id': str(uuid.uuid4()),
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get('status') != 'CAPTURED':
        errors = data.get('errors', [])
        raise RuntimeError(f'QBP charge declined: {errors}')

    return data['id']
