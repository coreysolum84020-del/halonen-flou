# tests/test_subscriptions.py

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

def test_subscribe_post_saves_subscriber(client, db, app):
    with app.app_context():
        from app.models import Subscriber
        Subscriber.query.delete()
        db.session.commit()

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
