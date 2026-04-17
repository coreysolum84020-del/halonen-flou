import time
import secrets
import requests
from urllib.parse import urlencode
from flask import redirect, request, current_app, session
from . import setup_bp

QBP_AUTH_URL = 'https://appcenter.intuit.com/connect/oauth2'
QBP_TOKEN_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
QBP_REDIRECT_URI = 'https://web-production-f4c2c.up.railway.app/setup/qbp/callback'


@setup_bp.route('/qbp')
def qbp_auth():
    state = secrets.token_urlsafe(16)
    session['qbp_oauth_state'] = state
    params = {
        'client_id': current_app.config['QBP_CLIENT_ID'],
        'redirect_uri': QBP_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'com.intuit.quickbooks.payment',
        'state': state,
    }
    return redirect(f"{QBP_AUTH_URL}?{urlencode(params)}")


@setup_bp.route('/qbp/callback')
def qbp_callback():
    code = request.args.get('code')
    if not code:
        return 'OAuth error: no code received.', 400

    state = request.args.get('state', '')
    if not state or state != session.pop('qbp_oauth_state', None):
        return 'OAuth error: invalid state parameter.', 400

    client_id = current_app.config['QBP_CLIENT_ID']
    client_secret = current_app.config['QBP_CLIENT_SECRET']

    try:
        resp = requests.post(
            QBP_TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': QBP_REDIRECT_URI,
            },
            auth=(client_id, client_secret),
            headers={'Accept': 'application/json'},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        expires_in = data['expires_in']
    except (requests.RequestException, ValueError, KeyError) as exc:
        current_app.logger.error('QBP OAuth token exchange failed: %s', exc)
        return 'OAuth error: token exchange failed.', 500

    from app.models import AppConfig
    from app.extensions import db

    def save(key, value):
        row = db.session.get(AppConfig, key)
        if row:
            row.value = value
        else:
            db.session.add(AppConfig(key=key, value=value))

    save('qbp_access_token', access_token)
    save('qbp_refresh_token', refresh_token)
    save('qbp_token_expiry', str(time.time() + expires_in))
    db.session.commit()

    return '<h1>QuickBooks Payments setup complete!</h1><p>You can close this window.</p>'
