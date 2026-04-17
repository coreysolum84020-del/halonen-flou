import time
import pytest
from unittest.mock import patch, MagicMock


def _mock_charge_ok(charge_id='ch_test_001'):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'id': charge_id,
        'status': 'CAPTURED',
        'amount': '100.00',
    }
    return mock


def _mock_charge_declined():
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'status': 'DECLINED',
        'errors': [{'code': 'PMT-4000', 'message': 'card declined'}],
    }
    return mock


def _mock_refresh_ok():
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'access_token': 'new_access_token',
        'refresh_token': 'new_refresh_token',
        'expires_in': 3600,
    }
    return mock


def _seed_tokens(app, db, expired=False):
    """Seed AppConfig with QBP tokens."""
    from app.models import AppConfig
    expiry = str(time.time() - 10 if expired else time.time() + 3600)
    with app.app_context():
        for key, value in [
            ('qbp_access_token', 'valid_access_token'),
            ('qbp_refresh_token', 'valid_refresh_token'),
            ('qbp_token_expiry', expiry),
        ]:
            db.session.merge(AppConfig(key=key, value=value))
        db.session.commit()


def test_charge_card_returns_charge_id(app, db):
    _seed_tokens(app, db)
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.qbp.requests.post',
                   return_value=_mock_charge_ok('ch_abc')) as mock_post:
            from app.blueprints.subscriptions.providers.qbp import charge_card
            charge_id = charge_card(
                name='Nova Raines',
                email='nova@music.com',
                service_type='lessons',
                amount=None,
                card_number='4111111111111111',
                exp_month='12',
                exp_year='2030',
                cvc='123',
            )
    assert charge_id == 'ch_abc'


def test_charge_card_raises_on_declined(app, db):
    _seed_tokens(app, db)
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.qbp.requests.post',
                   return_value=_mock_charge_declined()):
            from app.blueprints.subscriptions.providers.qbp import charge_card
            with pytest.raises(RuntimeError, match='declined'):
                charge_card(
                    name='Test',
                    email='t@t.com',
                    service_type='lessons',
                    amount=None,
                    card_number='4000000000000002',
                    exp_month='12',
                    exp_year='2030',
                    cvc='123',
                )


def test_charge_card_raises_when_no_tokens(app, db):
    with app.app_context():
        from app.blueprints.subscriptions.providers.qbp import charge_card
        with pytest.raises(RuntimeError, match='not configured'):
            charge_card(
                name='Test',
                email='t@t.com',
                service_type='lessons',
                amount=None,
                card_number='4111111111111111',
                exp_month='12',
                exp_year='2030',
                cvc='123',
            )


def test_get_access_token_refreshes_when_expired(app, db):
    _seed_tokens(app, db, expired=True)
    with app.app_context():
        with patch('app.blueprints.subscriptions.providers.qbp.requests.post',
                   return_value=_mock_refresh_ok()):
            from app.blueprints.subscriptions.providers.qbp import get_access_token
            token = get_access_token()
    assert token == 'new_access_token'
