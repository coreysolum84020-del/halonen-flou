import pytest
from datetime import datetime
from app.models import ContactMessage, Subscriber

def test_contact_message_creation(db, app):
    with app.app_context():
        msg = ContactMessage(
            name='John Doe',
            email='john@example.com',
            subject='Test inquiry',
            message='Hello there'
        )
        db.session.add(msg)
        db.session.commit()

        saved = ContactMessage.query.first()
        assert saved.name == 'John Doe'
        assert saved.email == 'john@example.com'
        assert saved.is_read == False
        assert isinstance(saved.created_at, datetime)

def test_subscriber_creation(db, app):
    with app.app_context():
        sub = Subscriber(
            email='artist@example.com',
            name='Nova Raines',
            service_type='promotion',
        )
        db.session.add(sub)
        db.session.commit()

        saved = Subscriber.query.first()
        assert saved.service_type == 'promotion'
        assert saved.status == 'pending'
        assert saved.plan_type == 'daily'

def test_subscriber_service_type_validation(app):
    with app.app_context():
        with pytest.raises(ValueError):
            Subscriber(
                email='test@example.com',
                name='Test Artist',
                service_type='invalid_type',
            )

def test_app_config_stores_value(app, db):
    from app.models import AppConfig
    with app.app_context():
        db.session.add(AppConfig(key='test_key', value='test_value'))
        db.session.commit()
        row = AppConfig.query.get('test_key')
        assert row.value == 'test_value'
