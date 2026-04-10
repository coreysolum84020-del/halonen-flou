# Wave Payment Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Wave payment processing so subscribers are redirected to a Wave-hosted checkout page and marked `active` after payment.

**Architecture:** A `wave.py` provider module handles all Wave API calls (create customer → create invoice → return checkout URL). The subscribe route calls it before saving to DB; if Wave fails, nothing is saved. A webhook endpoint receives payment confirmation and marks the subscriber active.

**Tech Stack:** Flask, SQLAlchemy, Wave GraphQL API (`gql.waveapps.com`), `requests` library, `unittest.mock` for tests.

---

## File Map

| File | Change |
|------|--------|
| `app/blueprints/subscriptions/providers/__init__.py` | Create — empty package marker |
| `app/blueprints/subscriptions/providers/wave.py` | Create — `create_invoice()` and `handle_webhook()` |
| `app/models.py` | Modify — add `wave_invoice_id` column to `Subscriber` |
| `app/config.py` | Modify — add `WAVE_API_TOKEN`, `WAVE_BUSINESS_ID` to all config classes |
| `app/blueprints/subscriptions/routes.py` | Modify — call Wave in subscribe POST; handle wave webhook |
| `requirements.txt` | Modify — add `requests==2.32.3` |
| `.env.example` | Modify — add Wave vars |
| `migrate_add_wave_invoice_id.py` | Create — one-shot column migration for production PostgreSQL |
| `tests/test_wave_provider.py` | Create — unit tests for wave.py |
| `tests/test_subscriptions.py` | Modify — mock Wave in subscribe POST test; add webhook test |

---

## Task 1: Add wave_invoice_id to Subscriber model

**Files:**
- Modify: `app/models.py`
- Modify: `app/config.py`
- Modify: `requirements.txt`
- Modify: `.env.example`
- Create: `migrate_add_wave_invoice_id.py`

- [ ] **Step 1: Add `requests` to requirements.txt**

Open `requirements.txt` and add after `psycopg2-binary==2.9.10`:
```
requests==2.32.3
```

- [ ] **Step 2: Install requests**

```bash
source venv/bin/activate && pip install requests==2.32.3
```

Expected: `Successfully installed requests-2.32.3` (or "already satisfied")

- [ ] **Step 3: Add Wave config to config.py**

Open `app/config.py`. Replace the entire file with:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WAVE_API_TOKEN = os.environ.get('WAVE_API_TOKEN', '')
    WAVE_BUSINESS_ID = os.environ.get('WAVE_BUSINESS_ID', '')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///halonen_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    _db_url = os.environ.get('DATABASE_URL', '')
    # Railway/Heroku provide postgres:// but SQLAlchemy requires postgresql://
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1) if _db_url else ''

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WAVE_API_TOKEN = 'test-wave-token'
    WAVE_BUSINESS_ID = 'test-wave-business-id'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
```

- [ ] **Step 4: Add `wave_invoice_id` to Subscriber model**

Open `app/models.py`. In the `Subscriber` class, add this line after `provider_customer_id`:

```python
    wave_invoice_id = db.Column(db.String(200), nullable=True)   # Wave invoice ID for payment tracking
```

- [ ] **Step 5: Update .env.example**

Open `.env.example` and add at the end:
```
WAVE_API_TOKEN=
WAVE_BUSINESS_ID=
```

- [ ] **Step 6: Create migration script for production**

Create `migrate_add_wave_invoice_id.py` at project root:

```python
"""
One-shot migration: adds wave_invoice_id column to subscribers table.
Run once on production: python migrate_add_wave_invoice_id.py
Safe to run multiple times (IF NOT EXISTS).
"""
import os
from app import create_app
from app.extensions import db
from sqlalchemy import text

env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS "
            "wave_invoice_id VARCHAR(200)"
        ))
        conn.commit()
    print("Done: wave_invoice_id column added to subscribers table.")
```

- [ ] **Step 7: Run tests — confirm nothing broken**

```bash
source venv/bin/activate && pytest tests/ -v
```

Expected: `33 passed`

- [ ] **Step 8: Commit**

```bash
git add app/models.py app/config.py requirements.txt .env.example migrate_add_wave_invoice_id.py
git commit -m "feat: add wave_invoice_id to Subscriber, Wave config keys"
```

---

## Task 2: Wave provider module

**Files:**
- Create: `app/blueprints/subscriptions/providers/__init__.py`
- Create: `app/blueprints/subscriptions/providers/wave.py`
- Create: `tests/test_wave_provider.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_wave_provider.py`:

```python
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
    # Second call is invoiceCreate — check unitPrice is '100.00'
    call_args = mock_post.call_args_list[1]
    body = call_args.kwargs.get('json') or call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs['json']
    items = body['variables']['input']['items']
    assert items[0]['unitPrice'] == '100.00'


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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
source venv/bin/activate && pytest tests/test_wave_provider.py -v
```

Expected: `ERROR` — module not found

- [ ] **Step 3: Create providers package**

Create `app/blueprints/subscriptions/providers/__init__.py` (empty file):

```python
```

- [ ] **Step 4: Create wave.py**

Create `app/blueprints/subscriptions/providers/wave.py`:

```python
import requests
from flask import current_app

WAVE_GQL_URL = 'https://gql.waveapps.com/graphql/public'

SERVICE_DESCRIPTIONS = {
    'promotion': 'Artist Promotion — Daily Subscription',
    'lessons': 'Music Lessons — 1-Hour Session',
    'production': 'Artist Production — Full Project',
}

SERVICE_PRICES = {
    'lessons': '100.00',
    'production': '2500.00',
}


def _gql(query, variables=None):
    token = current_app.config['WAVE_API_TOKEN']
    resp = requests.post(
        WAVE_GQL_URL,
        json={'query': query, 'variables': variables or {}},
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if 'errors' in data:
        raise RuntimeError(f"Wave API error: {data['errors']}")
    return data['data']


def create_invoice(name, email, service_type, custom_amount=None):
    """
    Creates a Wave customer and invoice for the given subscriber details.

    Returns:
        tuple: (invoice_id: str, checkout_url: str)

    Raises:
        RuntimeError: if Wave API returns input errors or HTTP errors.
    """
    business_id = current_app.config['WAVE_BUSINESS_ID']

    # Step 1: Create customer (Wave returns existing if email matches)
    customer_data = _gql(
        """
        mutation CreateCustomer($businessId: ID!, $input: CustomerCreateInput!) {
            customerCreate(businessId: $businessId, input: $input) {
                customer { id }
                inputErrors { message path code }
            }
        }
        """,
        {'businessId': business_id, 'input': {'name': name, 'email': email}},
    )
    errs = customer_data['customerCreate']['inputErrors']
    if errs:
        raise RuntimeError(f"Wave customer error: {errs}")
    customer_id = customer_data['customerCreate']['customer']['id']

    # Step 2: Determine unit price
    if service_type == 'promotion':
        unit_price = f'{float(custom_amount):.2f}'
    else:
        unit_price = SERVICE_PRICES[service_type]

    # Step 3: Create invoice
    invoice_data = _gql(
        """
        mutation CreateInvoice($businessId: ID!, $input: InvoiceCreateInput!) {
            invoiceCreate(businessId: $businessId, input: $input) {
                invoice { id viewUrl }
                inputErrors { message path code }
            }
        }
        """,
        {
            'businessId': business_id,
            'input': {
                'customerId': customer_id,
                'items': [{
                    'description': SERVICE_DESCRIPTIONS[service_type],
                    'quantity': '1',
                    'unitPrice': unit_price,
                }],
            },
        },
    )
    errs = invoice_data['invoiceCreate']['inputErrors']
    if errs:
        raise RuntimeError(f"Wave invoice error: {errs}")

    invoice = invoice_data['invoiceCreate']['invoice']
    return invoice['id'], invoice['viewUrl']


def handle_webhook(payload):
    """
    Processes a Wave webhook payload.
    Sets Subscriber.status = 'active' when the invoice status is PAID.

    Returns:
        bool: True if a subscriber was updated, False otherwise.
    """
    from app.models import Subscriber
    from app.extensions import db

    try:
        invoice_data = payload.get('data', {}).get('invoice', {})
        invoice_id = invoice_data.get('id')
        status = invoice_data.get('status')
    except AttributeError:
        return False

    if not invoice_id or status != 'PAID':
        return False

    sub = Subscriber.query.filter_by(wave_invoice_id=invoice_id).first()
    if sub is None or sub.status == 'active':
        return False

    sub.status = 'active'
    db.session.commit()
    return True
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
source venv/bin/activate && pytest tests/test_wave_provider.py -v
```

Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/subscriptions/providers/ tests/test_wave_provider.py
git commit -m "feat: Wave provider module — create_invoice and handle_webhook"
```

---

## Task 3: Wire Wave into subscribe route

**Files:**
- Modify: `app/blueprints/subscriptions/routes.py`
- Modify: `tests/test_subscriptions.py`

- [ ] **Step 1: Update test_subscribe_post_saves_subscriber to mock Wave**

Open `tests/test_subscriptions.py`. Replace `test_subscribe_post_saves_subscriber` with:

```python
from unittest.mock import patch, MagicMock

def _wave_mock():
    """Returns a mock requests.post that simulates successful Wave API calls."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.side_effect = [
        {'data': {'customerCreate': {'customer': {'id': 'cust_test'}, 'inputErrors': []}}},
        {'data': {'invoiceCreate': {'invoice': {'id': 'inv_test_123', 'viewUrl': 'https://wave.test/checkout'}, 'inputErrors': []}}},
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
```

Also add this new test at the end of the file:

```python
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
```

- [ ] **Step 2: Run updated tests — verify they fail**

```bash
source venv/bin/activate && pytest tests/test_subscriptions.py -v
```

Expected: `test_subscribe_post_saves_subscriber` FAILS (Wave not wired yet), new tests FAIL.

- [ ] **Step 3: Replace routes.py**

Replace the entire contents of `app/blueprints/subscriptions/routes.py` with:

```python
from flask import render_template, request, redirect, url_for, flash, jsonify
from . import subscriptions_bp
from app.extensions import db
from app.models import Subscriber

SERVICES = {
    'promotion': {'name': 'Artist Promotion', 'emoji': '📢', 'price': 'Your budget', 'daily': True},
    'lessons':   {'name': 'Music Lessons',    'emoji': '🎸', 'price': '$100/hour',    'daily': False},
    'production':{'name': 'Artist Production','emoji': '🎙️', 'price': '$2,500',       'daily': False},
}


@subscriptions_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def subscribe():
    errors = {}
    preselect = request.args.get('service', '')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        service_type = request.form.get('service_type', '').strip()
        custom_amount = request.form.get('custom_amount', '').strip()

        if not name:
            errors['name'] = 'Name is required.'
        if not email or '@' not in email:
            errors['email'] = 'Valid email required.'
        if service_type not in SERVICES:
            errors['service_type'] = 'Please select a service.'

        amount = None
        if not errors and custom_amount:
            try:
                amount = float(custom_amount)
                if amount <= 0:
                    errors['custom_amount'] = 'Budget must be a positive number.'
            except ValueError:
                errors['custom_amount'] = 'Budget must be a valid number.'

        if not errors:
            from .providers.wave import create_invoice
            try:
                invoice_id, checkout_url = create_invoice(
                    name=name,
                    email=email,
                    service_type=service_type,
                    custom_amount=amount,
                )
            except Exception:
                flash('Payment service temporarily unavailable. Please try again.', 'error')
                return render_template('subscriptions/subscribe.html',
                                       services=SERVICES,
                                       preselect=preselect,
                                       errors=errors,
                                       form_data=request.form)

            sub = Subscriber(
                name=name,
                email=email,
                service_type=service_type,
                custom_amount=amount,
                payment_provider='wave',
                wave_invoice_id=invoice_id,
            )
            db.session.add(sub)
            db.session.commit()
            return redirect(checkout_url)

    return render_template('subscriptions/subscribe.html',
                           services=SERVICES,
                           preselect=preselect,
                           errors=errors,
                           form_data=request.form)


@subscriptions_bp.route('/success')
def success():
    return render_template('subscriptions/success.html')


@subscriptions_bp.route('/cancel')
def cancel():
    return render_template('subscriptions/cancel.html')


@subscriptions_bp.route('/webhooks/<provider>', methods=['POST'])
def webhook(provider):
    """Payment provider webhook handler."""
    allowed = {'helcim', 'authorize', 'cashapp', 'quickbooks', 'melio', 'wave'}
    if provider not in allowed:
        return jsonify({'error': 'Unknown provider'}), 400

    payload = request.get_json(silent=True) or {}

    if provider == 'wave':
        from .providers.wave import handle_webhook
        handle_webhook(payload)

    return jsonify({'received': True, 'provider': provider}), 200
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
source venv/bin/activate && pytest tests/ -v
```

Expected: `41 passed`
- `tests/test_wave_provider.py`: 6 new tests
- `tests/test_subscriptions.py`: 7 existing + 2 new = 9 tests
- `tests/test_contact.py`: 8 tests
- `tests/test_main.py`: 7 tests
- `tests/test_models.py`: 3 tests
- `tests/test_services.py`: 8 tests
- Total: 41

- [ ] **Step 5: Commit**

```bash
git add app/blueprints/subscriptions/routes.py tests/test_subscriptions.py
git commit -m "feat: wire Wave payment into subscribe route and webhook handler"
```

---

## Task 4: Deploy to production

**Files:** none (config only)

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Set Wave env vars in Railway**

Run:

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer d9ffdf62-d621-417f-bfd9-b86bde3eb43e" \
  -H "Content-Type: application/json" \
  --data-raw '{"query":"mutation Upsert($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }","variables":{"input":{"projectId":"ca772102-1ddf-42a6-8cf9-8db4648d1ce2","environmentId":"807908e2-5c6e-434f-9aca-455b245ed738","serviceId":"89b803ed-6d0f-43ac-ab36-191f6c1c545c","variables":{"WAVE_API_TOKEN":"4uQqMcTFsojZ6U2AmxPAH4OHizdsOe","WAVE_BUSINESS_ID":"QnVzaW5lc3M6ZmZjMGJiZjEtMjhhZi00ODgyLWIwOTAtYWQyNjg1OGE5ZDFi"}}}}'
```

Expected: `{"data":{"variableCollectionUpsert":true}}`

- [ ] **Step 3: Run production migration**

After Railway redeploys, run migration via Railway exec or temporarily add a startup command.

The simplest approach — set a one-time `STARTUP_MIGRATION=1` var and add to `run.py`:

Actually, run it directly from the project directory with the Railway DATABASE_URL:

```bash
# Get DATABASE_URL from Railway and run migration locally
DATABASE_URL="<paste from Railway Variables>" FLASK_ENV=production python migrate_add_wave_invoice_id.py
```

Or connect to Railway's PostgreSQL directly:

```bash
# From Railway → Postgres service → Connect tab — get the public connection string
# Then run:
DATABASE_URL="postgresql://..." python migrate_add_wave_invoice_id.py
```

- [ ] **Step 4: Configure Wave webhook URL**

In Wave dashboard → Settings → Webhooks → Add webhook:
- URL: `https://web-production-f4c2c.up.railway.app/subscribe/webhooks/wave`
- Events: Invoice paid

- [ ] **Step 5: Verify deployment**

```bash
curl -s https://web-production-f4c2c.up.railway.app/subscribe | grep -c "Choose Your Service"
```

Expected: `1`

Test subscribe form end-to-end:
- Go to `https://web-production-f4c2c.up.railway.app/subscribe`
- Select a service, fill name + email
- Click "Continue to Payment"
- Should redirect to `next.waveapps.com/...` Wave hosted payment page
