def test_home_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200

def test_home_contains_brand(client):
    response = client.get('/')
    assert b'HALONEN FLOU' in response.data

def test_home_contains_hero_text(client):
    response = client.get('/')
    assert b'Artists Shine' in response.data

def test_about_returns_200(client):
    response = client.get('/about')
    assert response.status_code == 200

def test_about_contains_owner_name(client):
    response = client.get('/about')
    assert b'Brent Halonen' in response.data

def test_artists_returns_200(client):
    response = client.get('/artists')
    assert response.status_code == 200

def test_artists_contains_nova_raines(client):
    response = client.get('/artists')
    assert b'Nova Raines' in response.data
