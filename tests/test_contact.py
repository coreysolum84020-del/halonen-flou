def test_contact_page_returns_200(client):
    response = client.get('/contact')
    assert response.status_code == 200

def test_contact_page_shows_email(client):
    response = client.get('/contact')
    assert b'bluealikeu@gmail.com' in response.data

def test_contact_page_shows_phone(client):
    response = client.get('/contact')
    assert b'+19295039212' in response.data

def test_contact_form_submit_success(client, db, app):
    response = client.post('/contact', data={
        'name': 'John Artist',
        'email': 'john@music.com',
        'subject': 'Inquiry about promotion',
        'message': 'I want to promote my new single.',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your message has been sent' in response.data

def test_contact_form_saves_to_db(client, db, app):
    with app.app_context():
        from app.models import ContactMessage
        ContactMessage.query.delete()
        db.session.commit()

    client.post('/contact', data={
        'name': 'Test Artist',
        'email': 'test@example.com',
        'subject': 'Test subject',
        'message': 'Test message content here.',
    })

    with app.app_context():
        from app.models import ContactMessage
        msg = ContactMessage.query.first()
        assert msg is not None
        assert msg.name == 'Test Artist'
        assert msg.email == 'test@example.com'

def test_contact_form_empty_name_fails(client):
    response = client.post('/contact', data={
        'name': '',
        'email': 'test@example.com',
        'subject': 'Subject',
        'message': 'Message',
    })
    assert response.status_code == 200
    assert b'This field is required.' in response.data


def test_contact_form_repopulates_on_error(client):
    response = client.post('/contact', data={
        'name': 'Repop Test',
        'email': '',
        'subject': 'My Subject',
        'message': 'My message',
    })
    assert response.status_code == 200
    assert b'Repop Test' in response.data
    assert b'My Subject' in response.data


def test_contact_form_all_fields_empty_fails(client, db, app):
    from app.models import ContactMessage
    with app.app_context():
        count_before = ContactMessage.query.count()
    response = client.post('/contact', data={
        'name': '',
        'email': '',
        'subject': '',
        'message': '',
    })
    assert response.status_code == 200
    with app.app_context():
        assert ContactMessage.query.count() == count_before
