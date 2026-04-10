from unittest.mock import patch, MagicMock
import pytest


def _mock_wave_response(*json_payloads):
    """Returns a mock that serves json_payloads in sequence on each .json() call."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.side_effect = list(json_payloads)
    return mock


def test_create_invoice_returns_id_and_url(app):
    customer_resp = {
        'data': {
            'customerCreate': {
                'customer': {'id': 'cust_abc'},
                'inputErrors': [],
            }
        }
    }
    invoice_resp = {
        'data': {
            'invoiceCreate': {
                'invoice': {'id': 'inv_xyz', 'viewUrl': 'https://next.waveapps.com/pay/xyz'},
                'inputErrors': [],
            }
        }
    }
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.wave.requests.post',
                   return_value=_mock_wave_response(customer_resp, invoice_resp)):
            from app.blueprints.subscriptions.providers.wave import create_invoice
            invoice_id, url = create_invoice('Nova Raines', 'nova@music.com', 'promotion', custom_amount=200)
    assert invoice_id == 'inv_xyz'
    assert url == 'https://next.waveapps.com/pay/xyz'


def test_create_invoice_lessons_uses_fixed_price(app):
    customer_resp = {
        'data': {
            'customerCreate': {
                'customer': {'id': 'cust_abc'},
                'inputErrors': [],
            }
        }
    }
    invoice_resp = {
        'data': {
            'invoiceCreate': {
                'invoice': {'id': 'inv_lessons', 'viewUrl': 'https://next.waveapps.com/pay/lessons'},
                'inputErrors': [],
            }
        }
    }
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.wave.requests.post',
                   return_value=_mock_wave_response(customer_resp, invoice_resp)) as mock_post:
            from app.blueprints.subscriptions.providers.wave import create_invoice
            create_invoice('DJ Kaleo', 'dj@music.com', 'lessons')
    # Second call is invoiceCreate — check unitPrice is 100.00 (float)
    call_args = mock_post.call_args_list[1]
    items = call_args.kwargs['json']['variables']['input']['items']
    assert items[0]['unitPrice'] == 100.00


def test_create_invoice_raises_on_wave_customer_error(app):
    customer_resp = {
        'data': {
            'customerCreate': {
                'customer': None,
                'inputErrors': [{'message': 'Email invalid', 'path': 'email', 'code': 'INVALID'}],
            }
        }
    }
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.wave.requests.post',
                   return_value=_mock_wave_response(customer_resp)):
            from app.blueprints.subscriptions.providers.wave import create_invoice
            with pytest.raises(RuntimeError, match='Wave customer error'):
                create_invoice('Bad', 'notanemail', 'lessons')


def test_handle_webhook_marks_subscriber_active(app, db):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Test', email='t@t.com', service_type='lessons',
                         wave_invoice_id='inv_paid_123')
        db.session.add(sub)
        db.session.commit()

        from app.blueprints.subscriptions.providers.wave import handle_webhook
        result = handle_webhook({'data': {'invoice': {'id': 'inv_paid_123', 'status': 'PAID'}}})

        assert result is True
        updated = Subscriber.query.filter_by(wave_invoice_id='inv_paid_123').first()
        assert updated.status == 'active'


def test_handle_webhook_ignores_non_paid_status(app, db):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Test', email='t@t.com', service_type='lessons',
                         wave_invoice_id='inv_sent_456')
        db.session.add(sub)
        db.session.commit()

        from app.blueprints.subscriptions.providers.wave import handle_webhook
        result = handle_webhook({'data': {'invoice': {'id': 'inv_sent_456', 'status': 'SENT'}}})

        assert result is False
        unchanged = Subscriber.query.filter_by(wave_invoice_id='inv_sent_456').first()
        assert unchanged.status == 'pending'


def test_handle_webhook_ignores_unknown_invoice(app):
    with app.app_context():
        from app.blueprints.subscriptions.providers.wave import handle_webhook
        result = handle_webhook({'data': {'invoice': {'id': 'inv_unknown_999', 'status': 'PAID'}}})
        assert result is False
