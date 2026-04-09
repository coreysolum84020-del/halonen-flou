def test_services_overview_returns_200(client):
    response = client.get('/services')
    assert response.status_code == 200

def test_services_contains_three_services(client):
    response = client.get('/services')
    assert b'Promotion' in response.data
    assert b'Lessons' in response.data
    assert b'Production' in response.data

def test_promotion_page_returns_200(client):
    response = client.get('/services/promotion')
    assert response.status_code == 200

def test_promotion_page_shows_custom_price(client):
    response = client.get('/services/promotion')
    assert b'budget' in response.data.lower() or b'custom' in response.data.lower()

def test_lessons_page_returns_200(client):
    response = client.get('/services/lessons')
    assert response.status_code == 200

def test_lessons_page_shows_hourly_price(client):
    response = client.get('/services/lessons')
    assert b'100' in response.data

def test_production_page_returns_200(client):
    response = client.get('/services/production')
    assert response.status_code == 200

def test_production_page_shows_project_price(client):
    response = client.get('/services/production')
    assert b'2,500' in response.data
