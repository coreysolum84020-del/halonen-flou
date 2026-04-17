from unittest.mock import patch, MagicMock


def test_qbp_auth_route_redirects_to_intuit(client):
    response = client.get('/setup/qbp', follow_redirects=False)
    assert response.status_code == 302
    location = response.headers.get('Location', '')
    assert 'appcenter.intuit.com' in location
    assert 'com.intuit.quickbooks.payment' in location


def test_qbp_callback_saves_tokens(client, app, db):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'access_token': 'acc_tok_123',
        'refresh_token': 'ref_tok_456',
        'expires_in': 3600,
    }

    # Pre-populate session with expected state
    with client.session_transaction() as sess:
        sess['qbp_oauth_state'] = 'test_state_123'

    with patch('app.blueprints.setup.routes.requests.post', return_value=mock):
        response = client.get('/setup/qbp/callback?code=auth_code_abc&state=test_state_123')

    assert response.status_code == 200
    assert b'complete' in response.data.lower()

    with app.app_context():
        from app.models import AppConfig
        assert db.session.get(AppConfig, 'qbp_access_token').value == 'acc_tok_123'
        assert db.session.get(AppConfig, 'qbp_refresh_token').value == 'ref_tok_456'
