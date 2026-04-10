# tests/test_subscriptions.py
from unittest.mock import patch, MagicMock

def test_subscribe_page_returns_200(client):
    response = client.get('/subscribe')
    assert response.status_code == 200

def test_subscribe_page_shows_all_services(client):
    response = client.get('/subscribe')
    body = response.data.decode()
    assert 'promotion' in body.lower()
    assert 'lessons' in body.lower()
    assert 'production' in body.lower()

def test_subscribe_page_shows_daily_price(client):
    response = client.get('/subscribe')
    assert b'500' in response.data

def _wave_mock():
    """Returns a mock requests.post that simulates successful Wave API calls."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.side_effect = [
        {'data': {'customerCreate': {'customer': {'id': 'cust_test'}, 'inputErrors': []}}},
        {'data': {'invoiceCreate': {'invoice': {'id': 'inv_test_123', 'viewUrl': 'https://wave.test/checkout'}, 'inputErrors': []}}},
        {'data': {'invoiceApprove': {'didSucceed': True, 'inputErrors': []}}},
    ]
    return mock

def test_subscribe_post_saves_subscriber(client, db, app):
    with app.app_context():
        from app.models import Subscriber
        Subscriber.query.delete()
        db.session.commit()

    with patch('app.blueprints.subscriptions.providers.wave.requests.post',
               return_value=_wave_mock()):
        response = client.post('/subscribe', data={
            'name': 'Nova Raines',
            'email': 'nova@music.com',
            'service_type': 'promotion',
            'custom_amount': '200',
        }, follow_redirects=False)

    assert response.status_code == 302

    with app.app_context():
        from app.models import Subscriber
        sub = Subscriber.query.first()
        assert sub is not None
        assert sub.email == 'nova@music.com'
        assert sub.service_type == 'promotion'
        assert sub.status == 'pending'
        assert sub.wave_invoice_id == 'inv_test_123'
        assert sub.payment_provider == 'wave'

def test_success_page_returns_200(client):
    response = client.get('/subscribe/success')
    assert response.status_code == 200

def test_cancel_page_returns_200(client):
    response = client.get('/subscribe/cancel')
    assert response.status_code == 200

def test_webhook_endpoint_exists(client):
    response = client.post('/subscribe/webhooks/helcim',
                           json={'event': 'payment.success'},
                           content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['received'] is True
    assert data['provider'] == 'helcim'

def test_subscribe_post_wave_failure_shows_error(client):
    from unittest.mock import patch
    import requests as req
    with patch('app.blueprints.subscriptions.providers.wave.requests.post',
               side_effect=req.exceptions.ConnectionError('Wave down')):
        response = client.post('/subscribe', data={
            'name': 'Test User',
            'email': 'test@music.com',
            'service_type': 'lessons',
        }, follow_redirects=True)
    assert response.status_code == 200
    assert b'unavailable' in response.data.lower() or b'try again' in response.data.lower()


def test_webhook_wave_marks_subscriber_active(client, db, app):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Wave User', email='wave@test.com',
                         service_type='production', wave_invoice_id='inv_webhook_789')
        db.session.add(sub)
        db.session.commit()

    response = client.post('/subscribe/webhooks/wave',
                           json={'data': {'invoice': {'id': 'inv_webhook_789', 'status': 'PAID'}}},
                           content_type='application/json')
    assert response.status_code == 200

    with app.app_context():
        updated = Subscriber.query.filter_by(wave_invoice_id='inv_webhook_789').first()
        assert updated.status == 'active'
