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

def test_subscribe_page_shows_qbp_links(client):
    response = client.get('/subscribe')
    body = response.data.decode()
    assert 'connect.intuit.com' in body

def test_success_page_returns_200(client):
    response = client.get('/subscribe/success')
    assert response.status_code == 200

def test_cancel_page_returns_200(client):
    response = client.get('/subscribe/cancel')
    assert response.status_code == 200

def test_webhook_endpoint_exists(client):
    response = client.post('/subscribe/webhooks/wave',
                           json={'data': {'invoice': {'id': 'inv_x', 'status': 'DRAFT'}}},
                           content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['received'] is True
    assert data['provider'] == 'wave'
