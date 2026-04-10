# Email Notifications & Success Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Send email notifications to bluealikeu@gmail.com when a contact form is submitted or a subscriber's Wave payment is confirmed, and update the success page copy to reflect the new payment flow.

**Architecture:** Flask-Mail instance lives in `app/extensions.py` alongside `db` and `csrf`. A thin `app/email.py` wrapper exposes `send_notification(subject, body)` which catches all exceptions silently. Both trigger points (contact route, wave webhook) call it after their DB commit.

**Tech Stack:** Flask-Mail 0.9.1, Gmail SMTP (TLS port 587), unittest.mock for tests.

---

## File Map

| File | Change |
|------|--------|
| `requirements.txt` | Add `Flask-Mail==0.9.1` |
| `app/extensions.py` | Add `mail = Mail()` |
| `app/config.py` | Add MAIL_* and NOTIFY_EMAIL to all config classes |
| `app/__init__.py` | Import and init `mail` |
| `app/email.py` | Create — `send_notification(subject, body)` |
| `app/blueprints/contact/routes.py` | Call `send_notification` after commit |
| `app/blueprints/subscriptions/providers/wave.py` | Call `send_notification` in `handle_webhook` after commit |
| `app/templates/subscriptions/success.html` | Update copy to reflect Wave payment |
| `tests/test_email.py` | Create — 2 unit tests for `send_notification` |
| `tests/test_contact.py` | Add 1 test verifying notification is sent |
| `tests/test_wave_provider.py` | Add 1 test verifying notification is sent on webhook |

---

## Task 1: Flask-Mail setup

**Files:**
- Modify: `requirements.txt`
- Modify: `app/extensions.py`
- Modify: `app/config.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Add Flask-Mail to requirements.txt**

Open `requirements.txt`. Add after `requests==2.32.3`:
```
Flask-Mail==0.9.1
```

- [ ] **Step 2: Install Flask-Mail**

```bash
source venv/bin/activate && pip install Flask-Mail==0.9.1
```

Expected: `Successfully installed Flask-Mail-0.9.1` (or already satisfied)

- [ ] **Step 3: Add mail to extensions.py**

Replace the entire `app/extensions.py` with:

```python
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()
```

- [ ] **Step 4: Add MAIL config to config.py**

Replace the entire `app/config.py` with:

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
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', '')
    NOTIFY_EMAIL = os.environ.get('NOTIFY_EMAIL', '')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///halonen_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    _db_url = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1) if _db_url else ''

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WAVE_API_TOKEN = 'test-wave-token'
    WAVE_BUSINESS_ID = 'test-wave-business-id'
    MAIL_SUPPRESS_SEND = True
    NOTIFY_EMAIL = 'test@notify.com'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
```

- [ ] **Step 5: Init mail in app factory**

Replace the entire `app/__init__.py` with:

```python
from flask import Flask
from .config import config
from .extensions import db, csrf, mail

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    from .blueprints.main import main_bp
    from .blueprints.services import services_bp
    from .blueprints.contact import contact_bp
    from .blueprints.subscriptions import subscriptions_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(subscriptions_bp)

    from datetime import datetime

    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.now().year,
            'contact_email': 'bluealikeu@gmail.com',
            'contact_phone': '+19295039212',
        }

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app
```

- [ ] **Step 6: Run existing tests — all 41 must pass**

```bash
source venv/bin/activate && pytest tests/ -v --tb=short 2>&1 | tail -5
```

Expected: `41 passed`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt app/extensions.py app/config.py app/__init__.py
git commit -m "feat: add Flask-Mail to app setup"
```

---

## Task 2: send_notification function

**Files:**
- Create: `app/email.py`
- Create: `tests/test_email.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_email.py`:

```python
from unittest.mock import patch, MagicMock


def test_send_notification_sends_email(app):
    with app.app_context():
        with patch('app.email.mail.send') as mock_send:
            from app.email import send_notification
            send_notification('Test Subject', 'Test body text')
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][0]
    assert msg.subject == 'Test Subject'
    assert 'Test body text' in msg.body
    assert 'test@notify.com' in msg.recipients


def test_send_notification_silent_on_smtp_failure(app):
    with app.app_context():
        with patch('app.email.mail.send', side_effect=Exception('SMTP error')):
            from app.email import send_notification
            # Must not raise — failure is silent
            send_notification('Subject', 'Body')
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
source venv/bin/activate && pytest tests/test_email.py -v --tb=short
```

Expected: `ERROR` — `app.email` module not found

- [ ] **Step 3: Create app/email.py**

```python
from flask import current_app
from flask_mail import Message
from .extensions import mail


def send_notification(subject: str, body: str) -> None:
    """
    Sends a plain-text notification email to NOTIFY_EMAIL.
    Fails silently — never raises, never breaks the calling flow.
    """
    try:
        notify_email = current_app.config.get('NOTIFY_EMAIL', '')
        if not notify_email:
            return
        msg = Message(
            subject=subject,
            recipients=[notify_email],
            body=body,
        )
        mail.send(msg)
    except Exception:
        current_app.logger.error('Failed to send notification email', exc_info=True)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
source venv/bin/activate && pytest tests/test_email.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Run full suite**

```bash
source venv/bin/activate && pytest tests/ --tb=short -q 2>&1 | tail -3
```

Expected: `43 passed`

- [ ] **Step 6: Commit**

```bash
git add app/email.py tests/test_email.py
git commit -m "feat: send_notification helper using Flask-Mail"
```

---

## Task 3: Wire into contact route

**Files:**
- Modify: `app/blueprints/contact/routes.py`
- Modify: `tests/test_contact.py`

- [ ] **Step 1: Write failing test**

Open `tests/test_contact.py`. Add at the end of the file:

```python
def test_contact_form_sends_notification(client, db):
    from unittest.mock import patch
    with patch('app.blueprints.contact.routes.send_notification') as mock_notify:
        client.post('/contact', data={
            'name': 'Notify Test',
            'email': 'notify@music.com',
            'subject': 'Notification check',
            'message': 'Does this send an email?',
        })
    mock_notify.assert_called_once()
    call_kwargs = mock_notify.call_args
    subject_arg = call_kwargs[1].get('subject') or call_kwargs[0][0]
    body_arg = call_kwargs[1].get('body') or call_kwargs[0][1]
    assert 'Notify Test' in subject_arg
    assert 'notify@music.com' in body_arg
    assert 'Does this send an email?' in body_arg
```

- [ ] **Step 2: Run test — verify it fails**

```bash
source venv/bin/activate && pytest tests/test_contact.py::test_contact_form_sends_notification -v --tb=short
```

Expected: FAIL — `send_notification` not called (not yet wired)

- [ ] **Step 3: Update contact/routes.py**

Replace the entire `app/blueprints/contact/routes.py` with:

```python
import re
from flask import render_template, request, redirect, url_for, flash
from . import contact_bp
from app.extensions import db
from app.models import ContactMessage
from app.email import send_notification


@contact_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def contact():
    errors = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name:
            errors['name'] = 'This field is required.'
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors['email'] = 'A valid email address is required.'
        if not subject:
            errors['subject'] = 'This field is required.'
        if not message:
            errors['message'] = 'This field is required.'

        if not errors:
            msg = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            send_notification(
                subject=f'[HALONEN FLOU] New contact message from {name}',
                body=(
                    f'Name: {name}\n'
                    f'Email: {email}\n'
                    f'Subject: {subject}\n\n'
                    f'Message:\n{message}'
                ),
            )
            flash("Your message has been sent! We'll get back to you within 24 hours.", 'success')
            return redirect(url_for('contact.contact'))

    return render_template('contact.html', errors=errors, form_data=request.form)
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
source venv/bin/activate && pytest tests/ --tb=short -q 2>&1 | tail -3
```

Expected: `44 passed`

- [ ] **Step 5: Commit**

```bash
git add app/blueprints/contact/routes.py tests/test_contact.py
git commit -m "feat: send notification email on contact form submission"
```

---

## Task 4: Wire into wave webhook

**Files:**
- Modify: `app/blueprints/subscriptions/providers/wave.py`
- Modify: `tests/test_wave_provider.py`

- [ ] **Step 1: Write failing test**

Open `tests/test_wave_provider.py`. Add at the end of the file:

```python
def test_handle_webhook_sends_notification(app, db):
    from app.models import Subscriber
    with app.app_context():
        sub = Subscriber(name='Notify Sub', email='sub@music.com',
                         service_type='lessons', wave_invoice_id='inv_notify_001')
        db.session.add(sub)
        db.session.commit()

        from unittest.mock import patch
        with patch('app.blueprints.subscriptions.providers.wave.send_notification') as mock_notify:
            from app.blueprints.subscriptions.providers.wave import handle_webhook
            handle_webhook({'data': {'invoice': {'id': 'inv_notify_001', 'status': 'PAID'}}})

        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args
        subject_arg = call_kwargs[1].get('subject') or call_kwargs[0][0]
        body_arg = call_kwargs[1].get('body') or call_kwargs[0][1]
        assert 'Notify Sub' in subject_arg
        assert 'sub@music.com' in body_arg
```

- [ ] **Step 2: Run test — verify it fails**

```bash
source venv/bin/activate && pytest tests/test_wave_provider.py::test_handle_webhook_sends_notification -v --tb=short
```

Expected: FAIL — `send_notification` not called

- [ ] **Step 3: Update handle_webhook in wave.py**

Open `app/blueprints/subscriptions/providers/wave.py`. Add the import at the top of the file (after `from flask import current_app`):

```python
from app.email import send_notification
```

Then in `handle_webhook`, replace:

```python
    sub.status = 'active'
    db.session.commit()
    return True
```

with:

```python
    sub.status = 'active'
    db.session.commit()
    service_label = sub.service_type.capitalize()
    amount_info = f' — ${sub.custom_amount}' if sub.custom_amount else ''
    send_notification(
        subject=f'[HALONEN FLOU] New subscriber: {sub.name} ({service_label}{amount_info})',
        body=(
            f'Name: {sub.name}\n'
            f'Email: {sub.email}\n'
            f'Service: {service_label}{amount_info}\n'
        ),
    )
    return True
```

- [ ] **Step 4: Run all tests — verify they pass**

```bash
source venv/bin/activate && pytest tests/ --tb=short -q 2>&1 | tail -3
```

Expected: `45 passed`

- [ ] **Step 5: Commit**

```bash
git add app/blueprints/subscriptions/providers/wave.py tests/test_wave_provider.py
git commit -m "feat: send notification email when Wave payment confirmed"
```

---

## Task 5: Update success page

**Files:**
- Modify: `app/templates/subscriptions/success.html`

- [ ] **Step 1: Replace success.html**

Replace the entire `app/templates/subscriptions/success.html` with:

```html
{% extends 'base.html' %}
{% block title %}Payment Received!{% endblock %}

{% block content %}
<section class="section">
  <div class="container" style="text-align:center;max-width:480px;margin:0 auto;padding:60px 24px;">
    <div style="font-size:64px;margin-bottom:24px;" aria-hidden="true">🎉</div>
    <p class="section-eyebrow" style="margin-bottom:12px;">Subscription Confirmed</p>
    <h1 class="page-title" style="margin-bottom:16px;">Payment Received!</h1>
    <p class="page-subtitle" style="margin-bottom:32px;">Your payment was processed successfully. Thank you for choosing HALONEN FLOU — we'll be in touch within 24 hours to get everything started.</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a href="{{ url_for('main.artists') }}" class="btn btn-outline">See Artist Stories</a>
      <a href="{{ url_for('contact.contact') }}" class="btn btn-primary">Contact Us</a>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Run all tests**

```bash
source venv/bin/activate && pytest tests/ --tb=short -q 2>&1 | tail -3
```

Expected: `45 passed`

- [ ] **Step 3: Commit**

```bash
git add app/templates/subscriptions/success.html
git commit -m "fix: update success page copy to reflect Wave payment flow"
```

---

## Task 6: Deploy

**Files:** none (env vars only)

- [ ] **Step 1: Push to GitHub**

```bash
git push https://REDACTED_GITHUB_TOKEN@github.com/coreysolum84020-del/halonen-flou.git main
```

- [ ] **Step 2: Get Gmail App Password**

1. Go to myaccount.google.com → Security
2. Enable 2-Step Verification if not already on
3. Security → App Passwords → Select app: Mail, Select device: Other → type "halonen-flou" → Generate
4. Copy the 16-character password

- [ ] **Step 3: Set env vars in Railway**

```bash
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer d9ffdf62-d621-417f-bfd9-b86bde3eb43e" \
  -H "Content-Type: application/json" \
  --data-raw '{"query":"mutation Upsert($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }","variables":{"input":{"projectId":"ca772102-1ddf-42a6-8cf9-8db4648d1ce2","environmentId":"807908e2-5c6e-434f-9aca-455b245ed738","serviceId":"89b803ed-6d0f-43ac-ab36-191f6c1c545c","variables":{"MAIL_USERNAME":"bluealikeu@gmail.com","MAIL_PASSWORD":"<APP_PASSWORD_HERE>","NOTIFY_EMAIL":"bluealikeu@gmail.com"}}}}'
```

Replace `<APP_PASSWORD_HERE>` with the 16-char App Password from Step 2.

Expected: `{"data":{"variableCollectionUpsert":true}}`

- [ ] **Step 4: Verify deployment**

Wait ~2 minutes for Railway to redeploy, then:

```bash
curl -s https://web-production-f4c2c.up.railway.app/contact | grep -c "Contact"
```

Expected: `1` or more

- [ ] **Step 5: End-to-end test**

Submit the contact form at `https://web-production-f4c2c.up.railway.app/contact` with real data. Check `bluealikeu@gmail.com` inbox for notification within 30 seconds.
