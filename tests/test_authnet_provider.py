import pytest
from unittest.mock import patch, MagicMock


def _mock_authnet_ok(token='test_token_abc'):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'token': token,
        'messages': {'resultCode': 'Ok'},
    }
    return mock


def test_create_hosted_payment_returns_token(app):
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.authnet.requests.post',
                   return_value=_mock_authnet_ok('tok_xyz')):
            from app.blueprints.subscriptions.providers.authnet import create_hosted_payment
            token = create_hosted_payment('Nova Raines', 'nova@music.com', 'lessons', 'ref_001')
    assert token == 'tok_xyz'


def test_create_hosted_payment_lessons_uses_100(app):
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.authnet.requests.post',
                   return_value=_mock_authnet_ok()) as mock_post:
            from app.blueprints.subscriptions.providers.authnet import create_hosted_payment
            create_hosted_payment('Test', 'test@test.com', 'lessons', 'ref_002')
    body = mock_post.call_args.kwargs['json']
    amount = body['getHostedPaymentPageRequest']['transactionRequest']['amount']
    assert amount == '100.00'


def test_create_hosted_payment_promotion_uses_custom_amount(app):
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.authnet.requests.post',
                   return_value=_mock_authnet_ok()) as mock_post:
            from app.blueprints.subscriptions.providers.authnet import create_hosted_payment
            create_hosted_payment('Test', 'test@test.com', 'promotion', 'ref_003', custom_amount=250)
    body = mock_post.call_args.kwargs['json']
    amount = body['getHostedPaymentPageRequest']['transactionRequest']['amount']
    assert amount == '250.00'


def test_create_hosted_payment_raises_on_api_error(app):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'messages': {
            'resultCode': 'Error',
            'message': [{'text': 'Invalid credentials', 'code': 'E00007'}],
        }
    }
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.authnet.requests.post',
                   return_value=mock):
            from app.blueprints.subscriptions.providers.authnet import create_hosted_payment
            with pytest.raises(RuntimeError, match='Authorize.net error'):
                create_hosted_payment('Test', 'test@test.com', 'lessons', 'ref_004')


def test_handle_webhook_marks_subscriber_active(app, db):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Auth User', email='auth@test.com',
                         service_type='lessons', payment_provider='authorize',
                         provider_customer_id='ref_paid_001')
        db.session.add(sub)
        db.session.commit()

        from app.blueprints.subscriptions.providers.authnet import handle_webhook
        result = handle_webhook({'x_response_code': '1', 'x_invoice_num': 'ref_paid_001'})

        assert result is True
        updated = Subscriber.query.filter_by(provider_customer_id='ref_paid_001').first()
        assert updated.status == 'active'


def test_handle_webhook_ignores_declined(app, db):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Declined User', email='dec@test.com',
                         service_type='lessons', payment_provider='authorize',
                         provider_customer_id='ref_declined_001')
        db.session.add(sub)
        db.session.commit()

        from app.blueprints.subscriptions.providers.authnet import handle_webhook
        result = handle_webhook({'x_response_code': '2', 'x_invoice_num': 'ref_declined_001'})

        assert result is False
        unchanged = Subscriber.query.filter_by(provider_customer_id='ref_declined_001').first()
        assert unchanged.status == 'pending'
