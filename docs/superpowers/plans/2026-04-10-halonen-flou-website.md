# HALONEN FLOU Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Flask website for HALONEN FLOU music company with Neon Urban design, 5 pages, contact form, and payment-ready subscription stubs.

**Architecture:** Flask app-factory pattern with Blueprints per section (main, services, contact, subscriptions). SQLAlchemy for DB models. Jinja2 templates with a shared base layout. CSS-only Neon Urban theme (dark + purple/blue neon).

**Tech Stack:** Python 3.11+, Flask 3.x, Flask-SQLAlchemy, Flask-WTF, python-dotenv, pytest, SQLite (dev)

---

## File Map

| File | Responsibility |
|------|----------------|
| `run.py` | Entry point — creates app and runs dev server |
| `app/__init__.py` | App factory — creates Flask app, registers blueprints |
| `app/config.py` | Config classes: DevelopmentConfig, ProductionConfig |
| `app/extensions.py` | db, csrf singleton instances |
| `app/models.py` | ContactMessage, Subscriber SQLAlchemy models |
| `app/blueprints/main/routes.py` | GET / , /about, /artists |
| `app/blueprints/services/routes.py` | GET /services, /services/promotion, /services/lessons, /services/production |
| `app/blueprints/contact/routes.py` | GET+POST /contact |
| `app/blueprints/subscriptions/routes.py` | POST /subscribe, GET /subscribe/success, /subscribe/cancel, POST /webhooks/<provider> |
| `app/templates/base.html` | Shared layout: nav, footer, CSS/JS links |
| `app/templates/index.html` | Home page |
| `app/templates/about.html` | About page |
| `app/templates/artists.html` | Artists portfolio |
| `app/templates/services.html` | Services overview |
| `app/templates/services/promotion.html` | Promotion detail |
| `app/templates/services/lessons.html` | Lessons detail |
| `app/templates/services/production.html` | Production detail |
| `app/templates/contact.html` | Contact form |
| `app/templates/subscriptions/subscribe.html` | Subscribe form |
| `app/templates/subscriptions/success.html` | Confirmation page |
| `app/templates/subscriptions/cancel.html` | Cancellation page |
| `app/static/css/main.css` | Full Neon Urban theme |
| `app/static/js/main.js` | Scroll animations, sticky nav |
| `tests/conftest.py` | pytest fixtures: app, client, db |
| `tests/test_models.py` | Unit tests for models |
| `tests/test_main.py` | Route tests for main blueprint |
| `tests/test_services.py` | Route tests for services blueprint |
| `tests/test_contact.py` | Form submission tests |
| `tests/test_subscriptions.py` | Subscription stub tests |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `run.py`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/extensions.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p halonen-flou/app/blueprints/main
mkdir -p halonen-flou/app/blueprints/services
mkdir -p halonen-flou/app/blueprints/contact
mkdir -p halonen-flou/app/blueprints/subscriptions
mkdir -p halonen-flou/app/templates/services
mkdir -p halonen-flou/app/templates/subscriptions
mkdir -p halonen-flou/app/static/css
mkdir -p halonen-flou/app/static/js
mkdir -p halonen-flou/app/static/img
mkdir -p halonen-flou/tests
mkdir -p halonen-flou/docs/superpowers/specs
cd halonen-flou
```

- [ ] **Step 2: Create requirements.txt**

```
Flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
python-dotenv==1.0.1
WTForms==3.2.2
pytest==8.3.5
pytest-flask==1.3.0
```

- [ ] **Step 3: Install dependencies**

```bash
cd halonen-flou
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 4: Create .env.example**

```bash
# .env.example
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///halonen.db
FLASK_ENV=development
FLASK_DEBUG=1
```

- [ ] **Step 5: Create app/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///halonen_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    WTF_CSRF_ENABLED = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
```

- [ ] **Step 6: Create app/extensions.py**

```python
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()
```

- [ ] **Step 7: Create blueprint __init__.py files**

```python
# app/blueprints/main/__init__.py
from flask import Blueprint
main_bp = Blueprint('main', __name__)
from . import routes  # noqa: F401, E402
```

```python
# app/blueprints/services/__init__.py
from flask import Blueprint
services_bp = Blueprint('services', __name__, url_prefix='/services')
from . import routes  # noqa: F401, E402
```

```python
# app/blueprints/contact/__init__.py
from flask import Blueprint
contact_bp = Blueprint('contact', __name__, url_prefix='/contact')
from . import routes  # noqa: F401, E402
```

```python
# app/blueprints/subscriptions/__init__.py
from flask import Blueprint
subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/subscribe')
from . import routes  # noqa: F401, E402
```

- [ ] **Step 8: Create app/__init__.py (app factory)**

```python
from flask import Flask
from .config import config
from .extensions import db, csrf

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    csrf.init_app(app)

    from .blueprints.main import main_bp
    from .blueprints.services import services_bp
    from .blueprints.contact import contact_bp
    from .blueprints.subscriptions import subscriptions_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(subscriptions_bp)

    with app.app_context():
        db.create_all()

    return app
```

- [ ] **Step 9: Create run.py**

```python
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- [ ] **Step 10: Create tests/conftest.py**

```python
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def app():
    app = create_app('development')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db(app):
    return _db
```

- [ ] **Step 11: Create tests/__init__.py**

```python
```

- [ ] **Step 12: Verify app starts**

```bash
cd halonen-flou
python run.py
```

Expected: `* Running on http://0.0.0.0:5000` (routes will 404 until templates exist — that's fine)

- [ ] **Step 13: Commit**

```bash
git init
git add .
git commit -m "feat: flask app factory scaffold with blueprints and config"
```

---

## Task 2: Data Models

**Files:**
- Create: `app/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
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
        sub = Subscriber(
            email='test@example.com',
            name='Test Artist',
            service_type='invalid_type',
        )
        assert sub.service_type not in ['promotion', 'lessons', 'production']
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError: cannot import name 'ContactMessage'`

- [ ] **Step 3: Create app/models.py**

```python
from datetime import datetime
from .extensions import db

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ContactMessage from {self.name}>'

class Subscriber(db.Model):
    __tablename__ = 'subscribers'

    VALID_SERVICE_TYPES = ('promotion', 'lessons', 'production')

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)
    plan_type = db.Column(db.String(20), default='daily')
    status = db.Column(db.String(20), default='pending')
    custom_amount = db.Column(db.Numeric(10, 2), nullable=True)  # for promotion
    payment_provider = db.Column(db.String(50), nullable=True)   # helcim, authorize, etc.
    provider_customer_id = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscriber {self.name} ({self.service_type})>'
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add app/models.py tests/test_models.py
git commit -m "feat: add ContactMessage and Subscriber models"
```

---

## Task 3: Neon Urban CSS Theme

**Files:**
- Create: `app/static/css/main.css`

- [ ] **Step 1: Create app/static/css/main.css**

```css
/* ===== HALONEN FLOU — Neon Urban Theme ===== */

/* Reset & Base */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0a0a;
  --surface: #0d0d0d;
  --surface2: #120926;
  --primary: #8a2be2;
  --primary-glow: rgba(138, 43, 226, 0.5);
  --secondary: #00bfff;
  --secondary-glow: rgba(0, 191, 255, 0.4);
  --text: #ffffff;
  --text-muted: #999999;
  --text-dim: #555555;
  --border: rgba(138, 43, 226, 0.3);
  --border-blue: rgba(0, 191, 255, 0.3);
  --gradient: linear-gradient(135deg, var(--primary), var(--secondary));
  --font: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

html { scroll-behavior: smooth; }

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  overflow-x: hidden;
}

a { color: var(--primary); text-decoration: none; transition: color 0.2s; }
a:hover { color: var(--secondary); }

img { max-width: 100%; display: block; }

/* ===== NAVBAR ===== */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10, 10, 10, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: var(--primary);
  text-shadow: 0 0 15px var(--primary-glow);
  text-decoration: none;
}

.navbar-nav {
  display: flex;
  gap: 32px;
  list-style: none;
  align-items: center;
}

.navbar-nav a {
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text-muted);
  transition: color 0.2s;
}

.navbar-nav a:hover,
.navbar-nav a.active { color: var(--text); }

.btn-subscribe {
  background: var(--gradient);
  color: #fff !important;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  transition: opacity 0.2s, transform 0.2s;
}

.btn-subscribe:hover { opacity: 0.85; transform: translateY(-1px); }

/* Hamburger (mobile) */
.navbar-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  flex-direction: column;
  gap: 5px;
}
.navbar-toggle span {
  display: block;
  width: 24px;
  height: 2px;
  background: var(--text);
  transition: all 0.3s;
}

/* ===== BUTTONS ===== */
.btn {
  display: inline-block;
  padding: 12px 28px;
  border-radius: 25px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.25s;
  border: none;
}

.btn-primary {
  background: var(--gradient);
  color: #fff;
}
.btn-primary:hover { opacity: 0.85; transform: translateY(-2px); color: #fff; }

.btn-outline {
  background: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
}
.btn-outline:hover { background: rgba(138,43,226,0.1); color: var(--primary); }

.btn-lg { padding: 15px 36px; font-size: 13px; }

/* ===== HERO ===== */
.hero {
  position: relative;
  padding: 100px 40px 80px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--bg) 0%, var(--surface2) 50%, var(--bg) 100%);
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 25% 60%, rgba(138,43,226,0.18) 0%, transparent 55%),
    radial-gradient(ellipse at 75% 30%, rgba(0,191,255,0.10) 0%, transparent 50%);
}

.hero-content { position: relative; max-width: 580px; }

.hero-eyebrow {
  font-size: 10px;
  color: var(--primary);
  letter-spacing: 4px;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.hero-title {
  font-size: clamp(36px, 5vw, 58px);
  font-weight: 900;
  line-height: 1.05;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.hero-title .highlight {
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  max-width: 420px;
  margin-bottom: 32px;
  line-height: 1.7;
}

.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 48px; }

.hero-stats {
  display: flex;
  gap: 36px;
  flex-wrap: wrap;
}

.stat-number {
  font-size: 28px;
  font-weight: 900;
  color: var(--primary);
  text-shadow: 0 0 15px var(--primary-glow);
  line-height: 1;
}

.stat-number.blue {
  color: var(--secondary);
  text-shadow: 0 0 15px var(--secondary-glow);
}

.stat-label {
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-top: 4px;
}

/* Sound bar decoration */
.sound-bars {
  position: absolute;
  right: 80px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 120px;
  opacity: 0.5;
}

.sound-bars span {
  display: block;
  width: 5px;
  border-radius: 3px;
  background: var(--primary);
  animation: pulse 1.5s ease-in-out infinite;
}

.sound-bars span:nth-child(1) { height: 30%; animation-delay: 0s; }
.sound-bars span:nth-child(2) { height: 60%; animation-delay: 0.1s; }
.sound-bars span:nth-child(3) { height: 85%; animation-delay: 0.2s; }
.sound-bars span:nth-child(4) { height: 100%; animation-delay: 0.15s; }
.sound-bars span:nth-child(5) { height: 70%; animation-delay: 0.3s; background: var(--secondary); }
.sound-bars span:nth-child(6) { height: 45%; animation-delay: 0.25s; background: var(--secondary); }
.sound-bars span:nth-child(7) { height: 90%; animation-delay: 0.1s; }
.sound-bars span:nth-child(8) { height: 55%; animation-delay: 0.35s; }

@keyframes pulse {
  0%, 100% { transform: scaleY(1); opacity: 0.5; }
  50% { transform: scaleY(0.6); opacity: 0.8; }
}

/* ===== SECTIONS ===== */
.section {
  padding: 80px 40px;
}

.section-alt {
  background: rgba(138, 43, 226, 0.03);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.section-eyebrow {
  font-size: 10px;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: var(--primary);
  text-align: center;
  margin-bottom: 8px;
}

.section-eyebrow.blue { color: var(--secondary); }

.section-title {
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-align: center;
  margin-bottom: 48px;
}

.section-title.left { text-align: left; }

/* ===== NEON DIVIDER ===== */
.neon-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), var(--secondary), transparent);
  margin: 0;
}

/* ===== CARDS ===== */
.card-grid {
  display: grid;
  gap: 24px;
  max-width: 1100px;
  margin: 0 auto;
}

.card-grid-3 { grid-template-columns: repeat(3, 1fr); }
.card-grid-2 { grid-template-columns: repeat(2, 1fr); }

.card {
  background: rgba(138, 43, 226, 0.06);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px;
  transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s;
}

.card:hover {
  border-color: var(--primary);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(138, 43, 226, 0.2);
}

.card.blue-accent { border-color: var(--border-blue); }
.card.blue-accent:hover { border-color: var(--secondary); box-shadow: 0 8px 32px rgba(0,191,255,0.15); }

.card-icon { font-size: 36px; margin-bottom: 14px; }

.card-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.card-body { font-size: 13px; color: var(--text-muted); line-height: 1.6; }

.card-price {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  margin-top: 14px;
}

.card-price.blue { color: var(--secondary); }

/* ===== ARTIST CARDS ===== */
.artist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  max-width: 1100px;
  margin: 0 auto;
}

.artist-card {
  background: linear-gradient(160deg, var(--surface2), var(--surface));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 24px 16px;
  text-align: center;
  transition: all 0.3s;
}

.artist-card:hover {
  border-color: var(--primary);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px var(--primary-glow);
}

.artist-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--gradient);
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.artist-name { font-size: 14px; font-weight: 700; margin-bottom: 4px; }

.artist-genre { font-size: 11px; color: var(--text-muted); margin-bottom: 10px; }

.artist-metric { font-size: 12px; font-weight: 700; color: var(--primary); }
.artist-metric.blue { color: var(--secondary); }

/* ===== CTA BANNER ===== */
.cta-banner {
  position: relative;
  padding: 72px 40px;
  background: linear-gradient(135deg, var(--surface2), var(--bg));
  text-align: center;
  overflow: hidden;
}

.cta-banner::before {
  content: '';
  position: absolute;
  top: 0; left: 50%;
  transform: translateX(-50%);
  width: 400px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), var(--secondary), transparent);
}

.cta-banner::after {
  content: '';
  position: absolute;
  bottom: 0; left: 50%;
  transform: translateX(-50%);
  width: 400px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), var(--secondary), transparent);
}

.cta-eyebrow { font-size: 10px; color: var(--primary); letter-spacing: 4px; text-transform: uppercase; margin-bottom: 12px; }

.cta-title { font-size: clamp(24px, 3.5vw, 38px); font-weight: 900; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }

.cta-subtitle { font-size: 14px; color: var(--text-muted); max-width: 440px; margin: 0 auto 32px; }

.cta-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

/* ===== FORMS ===== */
.form-group { margin-bottom: 20px; }

.form-label {
  display: block;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.form-control {
  width: 100%;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  color: var(--text);
  font-size: 14px;
  font-family: var(--font);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(138,43,226,0.15);
}

.form-control::placeholder { color: var(--text-dim); }

textarea.form-control { resize: vertical; min-height: 130px; }

.form-error { font-size: 12px; color: #ff6b6b; margin-top: 4px; }

.flash-success {
  background: rgba(0,191,255,0.1);
  border: 1px solid var(--border-blue);
  color: var(--secondary);
  padding: 14px 20px;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 13px;
}

.flash-error {
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.3);
  color: #ff6b6b;
  padding: 14px 20px;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 13px;
}

/* ===== FAQ ===== */
.faq-item {
  border-bottom: 1px solid var(--border);
  padding: 20px 0;
}

.faq-question {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.faq-question::after { content: '+'; color: var(--primary); font-size: 20px; }
.faq-item.open .faq-question::after { content: '−'; }

.faq-answer {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.7;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, padding 0.3s;
}

.faq-item.open .faq-answer { max-height: 300px; padding-top: 12px; }

/* ===== SERVICE DETAIL ===== */
.service-hero {
  padding: 80px 40px 60px;
  background: linear-gradient(135deg, var(--surface2), var(--bg));
  border-bottom: 1px solid var(--border);
}

.includes-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.includes-list li {
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 10px;
}

.includes-list li::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--primary);
  flex-shrink: 0;
}

.price-badge {
  display: inline-block;
  background: var(--gradient);
  color: #fff;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 24px;
}

/* Custom price input */
.price-input-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}
.price-input-wrapper::before {
  content: '$';
  position: absolute;
  left: 14px;
  color: var(--primary);
  font-weight: 700;
  font-size: 16px;
}
.price-input-wrapper .form-control { padding-left: 30px; width: 160px; }

/* ===== ABOUT ===== */
.about-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 60px;
  align-items: start;
  max-width: 900px;
  margin: 0 auto;
}

.about-portrait {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--surface2), var(--primary) 60%, var(--secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72px;
  border: 1px solid var(--border);
}

.about-name { font-size: 26px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; }
.about-title { font-size: 12px; color: var(--primary); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 20px; }
.about-bio { font-size: 14px; color: var(--text-muted); line-height: 1.8; }

.values-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.value-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.value-icon { font-size: 32px; margin-bottom: 10px; }
.value-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.value-text { font-size: 12px; color: var(--text-muted); line-height: 1.6; }

/* Timeline */
.timeline { max-width: 600px; margin: 0 auto; position: relative; padding-left: 32px; }
.timeline::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 1px; background: var(--border); }

.timeline-item { position: relative; padding-bottom: 36px; }
.timeline-item::before { content: ''; position: absolute; left: -36px; top: 5px; width: 10px; height: 10px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 8px var(--primary-glow); }

.timeline-year { font-size: 10px; color: var(--primary); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }
.timeline-text { font-size: 13px; color: var(--text-muted); line-height: 1.6; }

/* ===== CONTACT ===== */
.contact-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 60px;
  max-width: 900px;
  margin: 0 auto;
}

.contact-info-item {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
  font-size: 14px;
  color: var(--text-muted);
}

.contact-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(138,43,226,0.1);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

/* ===== SUBSCRIBE PAGE ===== */
.subscribe-container {
  max-width: 520px;
  margin: 60px auto;
  padding: 0 40px;
}

.subscribe-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
}

.service-select-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.service-option {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.service-option:hover,
.service-option.selected {
  border-color: var(--primary);
  background: rgba(138,43,226,0.1);
}

.service-option input[type="radio"] { display: none; }
.service-option-icon { font-size: 22px; margin-bottom: 4px; }
.service-option-name { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.service-option-price { font-size: 11px; color: var(--primary); margin-top: 2px; }

/* ===== FOOTER ===== */
.footer {
  padding: 28px 40px;
  border-top: 1px solid rgba(255,255,255,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.footer-copy { font-size: 12px; color: var(--text-dim); }

.footer-links {
  display: flex;
  gap: 24px;
  list-style: none;
}

.footer-links a { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; text-transform: uppercase; }
.footer-links a:hover { color: var(--text-muted); }

.footer-contact { font-size: 12px; color: var(--text-dim); }

/* ===== PAGE HEADER (inner pages) ===== */
.page-header {
  padding: 60px 40px 50px;
  background: linear-gradient(135deg, var(--surface2), var(--bg));
  border-bottom: 1px solid var(--border);
}

.page-title {
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 10px;
}

.page-subtitle { font-size: 14px; color: var(--text-muted); max-width: 500px; }

/* ===== UTILITIES ===== */
.container { max-width: 1100px; margin: 0 auto; }
.text-center { text-align: center; }
.mt-8 { margin-top: 8px; }
.mt-16 { margin-top: 16px; }
.mt-24 { margin-top: 24px; }
.mt-40 { margin-top: 40px; }

/* Fade-in animation */
.fade-in { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
.fade-in.visible { opacity: 1; transform: translateY(0); }

/* ===== RESPONSIVE ===== */
@media (max-width: 900px) {
  .card-grid-3 { grid-template-columns: 1fr 1fr; }
  .about-grid { grid-template-columns: 1fr; }
  .contact-grid { grid-template-columns: 1fr; }
  .values-grid { grid-template-columns: 1fr 1fr; }
  .sound-bars { display: none; }
}

@media (max-width: 640px) {
  .navbar { padding: 0 20px; }
  .navbar-nav { display: none; position: absolute; top: 64px; left: 0; right: 0; background: var(--surface); flex-direction: column; padding: 20px; border-bottom: 1px solid var(--border); }
  .navbar-nav.open { display: flex; }
  .navbar-toggle { display: flex; }
  .hero { padding: 60px 20px; }
  .section { padding: 60px 20px; }
  .card-grid-3 { grid-template-columns: 1fr; }
  .card-grid-2 { grid-template-columns: 1fr; }
  .values-grid { grid-template-columns: 1fr; }
  .service-select-grid { grid-template-columns: 1fr; }
  .footer { flex-direction: column; text-align: center; }
  .artist-grid { grid-template-columns: repeat(2, 1fr); }
  .subscribe-card { padding: 24px 20px; }
}
```

- [ ] **Step 2: Commit**

```bash
git add app/static/css/main.css
git commit -m "feat: add full Neon Urban CSS theme"
```

---

## Task 4: Base Template

**Files:**
- Create: `app/templates/base.html`
- Create: `app/static/js/main.js`

- [ ] **Step 1: Create app/templates/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}HALONEN FLOU{% endblock %} — Music · Production · Promotion</title>
  <meta name="description" content="{% block meta_description %}HALONEN FLOU — Professional music promotion, lessons, and artist production services.{% endblock %}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body>

  <nav class="navbar">
    <a href="{{ url_for('main.index') }}" class="navbar-brand">HALONEN FLOU</a>
    <button class="navbar-toggle" id="navToggle" aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
    <ul class="navbar-nav" id="navMenu">
      <li><a href="{{ url_for('main.index') }}" {% if request.endpoint == 'main.index' %}class="active"{% endif %}>Home</a></li>
      <li><a href="{{ url_for('main.about') }}" {% if request.endpoint == 'main.about' %}class="active"{% endif %}>About</a></li>
      <li><a href="{{ url_for('services.overview') }}" {% if request.blueprint == 'services' %}class="active"{% endif %}>Services</a></li>
      <li><a href="{{ url_for('main.artists') }}" {% if request.endpoint == 'main.artists' %}class="active"{% endif %}>Artists</a></li>
      <li><a href="{{ url_for('contact.contact') }}" {% if request.blueprint == 'contact' %}class="active"{% endif %}>Contact</a></li>
      <li><a href="{{ url_for('subscriptions.subscribe') }}" class="btn-subscribe">Subscribe</a></li>
    </ul>
  </nav>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <div style="padding: 0 40px; margin-top: 16px;">
        {% for category, message in messages %}
          <div class="flash-{{ category }}">{{ message }}</div>
        {% endfor %}
      </div>
    {% endif %}
  {% endwith %}

  <main>
    {% block content %}{% endblock %}
  </main>

  <div class="neon-divider"></div>
  <footer class="footer">
    <div class="footer-copy">© 2025 HALONEN FLOU. All rights reserved.</div>
    <ul class="footer-links">
      <li><a href="{{ url_for('main.about') }}">About</a></li>
      <li><a href="{{ url_for('services.overview') }}">Services</a></li>
      <li><a href="{{ url_for('contact.contact') }}">Contact</a></li>
    </ul>
    <div class="footer-contact">bluealikeu@gmail.com</div>
  </footer>

  <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

- [ ] **Step 2: Create app/static/js/main.js**

```javascript
// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => navMenu.classList.toggle('open'));
}

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(question => {
  question.addEventListener('click', () => {
    const item = question.parentElement;
    item.classList.toggle('open');
  });
});

// Service option radio cards
document.querySelectorAll('.service-option').forEach(option => {
  option.addEventListener('click', () => {
    document.querySelectorAll('.service-option').forEach(o => o.classList.remove('selected'));
    option.classList.add('selected');
    const radio = option.querySelector('input[type="radio"]');
    if (radio) radio.checked = true;

    // Show/hide custom price input
    const customPriceGroup = document.getElementById('customPriceGroup');
    if (customPriceGroup) {
      customPriceGroup.style.display = radio && radio.value === 'promotion' ? 'block' : 'none';
    }
  });
});

// Fade-in on scroll
const fadeEls = document.querySelectorAll('.fade-in');
if (fadeEls.length) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  fadeEls.forEach(el => observer.observe(el));
}
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/base.html app/static/js/main.js
git commit -m "feat: base template with sticky nav, flash messages, footer and JS"
```

---

## Task 5: Main Blueprint — Home, About, Artists

**Files:**
- Create: `app/blueprints/main/routes.py`
- Create: `app/templates/index.html`
- Create: `app/templates/about.html`
- Create: `app/templates/artists.html`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_main.py

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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `FAILED` — routes don't exist yet.

- [ ] **Step 3: Create app/blueprints/main/routes.py**

```python
from flask import render_template
from . import main_bp

ARTISTS = [
    {
        'name': 'Nova Raines',
        'emoji': '🎤',
        'genre': 'R&B · Soul',
        'service': 'Promotion',
        'metric': '+340% streams',
        'metric_color': 'purple',
        'story': 'Nova came to us as an unsigned indie artist with raw talent and zero online presence. Within 3 months of our daily promotion package, her Spotify streams increased by 340%. We ran targeted social campaigns, pitched her to 40+ playlists, and built a loyal fanbase from scratch.',
    },
    {
        'name': 'DJ Kaleo',
        'emoji': '🎧',
        'genre': 'Electronic · House',
        'service': 'Production',
        'metric': 'Signed to label',
        'metric_color': 'blue',
        'story': 'Kaleo had the beats but needed professional polish. Our production team worked with him for 6 weeks — studio sessions, mixing, mastering, and artist development. The resulting EP caught the attention of a major label A&R, leading to a full recording deal.',
    },
    {
        'name': 'Zara Vex',
        'emoji': '🎸',
        'genre': 'Alt-Rock · Indie',
        'service': 'Promotion',
        'metric': '50K followers',
        'metric_color': 'purple',
        'story': "Zara's alternative sound needed the right audience. We crafted a 90-day promotion strategy combining Instagram Reels campaigns, press outreach to music blogs, and Spotify editorial pitching. She gained 50K engaged Instagram followers and landed features in three music publications.",
    },
    {
        'name': 'Marcus Cole',
        'emoji': '🎙️',
        'genre': 'Hip-Hop',
        'service': 'Lessons + Production',
        'metric': 'Debut album',
        'metric_color': 'purple',
        'story': "Marcus enrolled in our music production lessons and simultaneously worked with our production team. In 8 months, he went from learning DAW basics to releasing a fully-produced 10-track debut album that charted on regional hip-hop charts.",
    },
    {
        'name': 'Lia Frost',
        'emoji': '🌟',
        'genre': 'Pop',
        'service': 'Promotion',
        'metric': '2M TikTok views',
        'metric_color': 'blue',
        'story': "Lia had one great single but no visibility. We identified the TikTok trend angle, crafted the campaign, coordinated with 12 content creators, and ran paid micro-targeting. One video went viral with 2M views, pushing the single into the Spotify Viral 50 chart.",
    },
]

@main_bp.route('/')
def index():
    featured = ARTISTS[:3]
    return render_template('index.html', featured_artists=featured)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/artists')
def artists():
    return render_template('artists.html', artists=ARTISTS)
```

- [ ] **Step 4: Create app/templates/index.html**

```html
{% extends 'base.html' %}

{% block title %}Home{% endblock %}

{% block content %}
<!-- HERO -->
<section class="hero">
  <div class="hero-content fade-in">
    <p class="hero-eyebrow">🎵 Music · Production · Promotion</p>
    <h1 class="hero-title">We Make<br><span class="highlight">Artists Shine.</span></h1>
    <p class="hero-subtitle">From raw talent to world-class performance — HALONEN FLOU provides everything artists need to grow, learn, and be heard.</p>
    <div class="hero-actions">
      <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary btn-lg">Start Today</a>
      <a href="{{ url_for('main.artists') }}" class="btn btn-outline btn-lg">See Artists →</a>
    </div>
    <div class="hero-stats">
      <div><div class="stat-number">50+</div><div class="stat-label">Artists</div></div>
      <div><div class="stat-number blue">3</div><div class="stat-label">Services</div></div>
      <div><div class="stat-number">5★</div><div class="stat-label">Rated</div></div>
      <div><div class="stat-number blue">10y</div><div class="stat-label">Experience</div></div>
    </div>
  </div>
  <div class="sound-bars" aria-hidden="true">
    <span></span><span></span><span></span><span></span>
    <span></span><span></span><span></span><span></span>
  </div>
</section>

<div class="neon-divider"></div>

<!-- SERVICES PREVIEW -->
<section class="section">
  <p class="section-eyebrow">What We Do</p>
  <h2 class="section-title">Our Services</h2>
  <div class="card-grid card-grid-3 container">
    <div class="card fade-in">
      <div class="card-icon">📢</div>
      <div class="card-title">Artist Promotion</div>
      <div class="card-body">Social media campaigns, playlist pitching, press coverage & PR strategies tailored to your sound.</div>
      <div class="card-price">Custom budget →</div>
      <a href="{{ url_for('services.promotion') }}" class="btn btn-outline" style="margin-top:16px;font-size:11px;padding:8px 18px;">Learn More</a>
    </div>
    <div class="card blue-accent fade-in">
      <div class="card-icon">🎸</div>
      <div class="card-title">Music Lessons</div>
      <div class="card-body">Guitar, piano, voice, music production. Expert instructors for all skill levels, from beginner to pro.</div>
      <div class="card-price blue">$100 / hour →</div>
      <a href="{{ url_for('services.lessons') }}" class="btn btn-outline" style="margin-top:16px;font-size:11px;padding:8px 18px;">Learn More</a>
    </div>
    <div class="card fade-in">
      <div class="card-icon">🎙️</div>
      <div class="card-title">Artist Production</div>
      <div class="card-body">Full studio production, mixing, mastering & complete artist development from concept to release.</div>
      <div class="card-price">$2,500 / project →</div>
      <a href="{{ url_for('services.production') }}" class="btn btn-outline" style="margin-top:16px;font-size:11px;padding:8px 18px;">Learn More</a>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<!-- FEATURED ARTISTS -->
<section class="section section-alt">
  <p class="section-eyebrow blue">Success Stories</p>
  <h2 class="section-title">Featured Artists</h2>
  <div class="artist-grid">
    {% for artist in featured_artists %}
    <div class="artist-card fade-in">
      <div class="artist-avatar">{{ artist.emoji }}</div>
      <div class="artist-name">{{ artist.name }}</div>
      <div class="artist-genre">{{ artist.genre }}</div>
      <div class="artist-metric {% if artist.metric_color == 'blue' %}blue{% endif %}">{{ artist.metric }}</div>
    </div>
    {% endfor %}
  </div>
  <div class="text-center mt-40">
    <a href="{{ url_for('main.artists') }}" class="btn btn-outline">View All Artists →</a>
  </div>
</section>

<div class="neon-divider"></div>

<!-- CTA BANNER -->
<section class="cta-banner">
  <p class="cta-eyebrow">Daily Subscription</p>
  <h2 class="cta-title">Ready to Start?</h2>
  <p class="cta-subtitle">Subscribe today and get access to professional music services. No long-term commitment required.</p>
  <div class="cta-actions">
    <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary btn-lg">Get Started Now</a>
    <a href="{{ url_for('contact.contact') }}" class="btn btn-outline btn-lg">Ask a Question</a>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 5: Create app/templates/about.html**

```html
{% extends 'base.html' %}

{% block title %}About{% endblock %}
{% block meta_description %}Learn about Brent Halonen and the mission behind HALONEN FLOU music company.{% endblock %}

{% block content %}
<div class="page-header">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Our Story</p>
  <h1 class="page-title">About HALONEN FLOU</h1>
  <p class="page-subtitle">Built by a musician, for musicians. We understand the journey because we've lived it.</p>
</div>

<!-- FOUNDER -->
<section class="section">
  <div class="about-grid">
    <div>
      <div class="about-portrait">👨‍🎤</div>
    </div>
    <div>
      <div class="about-name">Brent Halonen</div>
      <div class="about-title">Founder & CEO</div>
      <p class="about-bio">Brent Halonen has spent over a decade at the intersection of music, technology, and marketing. Starting as a session guitarist in New York City, he quickly realized that talent alone wasn't enough — artists needed a strategic partner who understood both the creative and business sides of music.</p>
      <p class="about-bio" style="margin-top:16px;">He founded HALONEN FLOU with a single mission: to give every artist — regardless of budget or background — access to world-class promotion, education, and production. Today, the company has worked with over 50 artists across genres and continues to grow.</p>
      <div style="display:flex;gap:16px;margin-top:24px;flex-wrap:wrap;">
        <a href="mailto:bluealikeu@gmail.com" class="btn btn-primary">Get in Touch</a>
        <a href="tel:+19295039212" class="btn btn-outline">+1 929 503 9212</a>
      </div>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<!-- MISSION -->
<section class="section section-alt">
  <p class="section-eyebrow">What Drives Us</p>
  <h2 class="section-title">Mission & Values</h2>
  <div class="values-grid">
    <div class="value-card fade-in">
      <div class="value-icon">🎯</div>
      <div class="value-title">Artist First</div>
      <div class="value-text">Every decision we make starts with one question: does this serve the artist? We build strategies around your unique sound and vision, not cookie-cutter templates.</div>
    </div>
    <div class="value-card fade-in">
      <div class="value-icon">🔥</div>
      <div class="value-title">Results-Driven</div>
      <div class="value-text">We measure success by your growth — streams, followers, deals, releases. Our daily subscription model means we're invested in your progress every single day.</div>
    </div>
    <div class="value-card fade-in">
      <div class="value-icon">🤝</div>
      <div class="value-title">True Partnership</div>
      <div class="value-text">We don't just deliver a service — we become your team. Transparent communication, honest feedback, and real collaboration at every step of your journey.</div>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<!-- TIMELINE -->
<section class="section">
  <p class="section-eyebrow blue">Our Journey</p>
  <h2 class="section-title">How We Got Here</h2>
  <div class="timeline">
    <div class="timeline-item fade-in">
      <div class="timeline-year">2014</div>
      <div class="timeline-text">Brent Halonen begins his career as a session guitarist and music producer in New York City, working with emerging artists across genres.</div>
    </div>
    <div class="timeline-item fade-in">
      <div class="timeline-year">2017</div>
      <div class="timeline-text">After managing promotion for 10+ artists independently, Brent formalizes the approach and launches the first version of HALONEN FLOU as a boutique agency.</div>
    </div>
    <div class="timeline-item fade-in">
      <div class="timeline-year">2019</div>
      <div class="timeline-text">Expansion into music education — structured lesson programs for guitar, piano, voice, and music production added to the service portfolio.</div>
    </div>
    <div class="timeline-item fade-in">
      <div class="timeline-year">2022</div>
      <div class="timeline-text">Full artist production services launched. First artist signed to a major label after using HALONEN FLOU production and promotion packages.</div>
    </div>
    <div class="timeline-item fade-in">
      <div class="timeline-year">2025</div>
      <div class="timeline-text">50+ artists served across R&B, Hip-Hop, Electronic, Rock and Pop. Daily subscription model introduced to make professional services accessible to every artist.</div>
    </div>
  </div>
</section>

<div class="neon-divider"></div>
<section class="cta-banner">
  <p class="cta-eyebrow">Work With Us</p>
  <h2 class="cta-title">Let's Build Something.</h2>
  <p class="cta-subtitle">Ready to take your music to the next level? Start with a conversation.</p>
  <div class="cta-actions">
    <a href="{{ url_for('contact.contact') }}" class="btn btn-primary btn-lg">Contact Brent</a>
    <a href="{{ url_for('services.overview') }}" class="btn btn-outline btn-lg">View Services</a>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 6: Create app/templates/artists.html**

```html
{% extends 'base.html' %}

{% block title %}Artists{% endblock %}
{% block meta_description %}Success stories from artists who grew with HALONEN FLOU — promotion, lessons, and production.{% endblock %}

{% block content %}
<div class="page-header">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Success Stories</p>
  <h1 class="page-title">Our Artists</h1>
  <p class="page-subtitle">Real results from real artists. Here's how HALONEN FLOU helped them grow.</p>
</div>

<section class="section">
  <div class="container">
    {% for artist in artists %}
    <div style="background: rgba(138,43,226,0.05); border: 1px solid {% if loop.index is odd %}var(--border){% else %}var(--border-blue){% endif %}; border-radius: 16px; padding: 36px; margin-bottom: 28px; display: grid; grid-template-columns: auto 1fr; gap: 36px; align-items: start;" class="fade-in">
      <div style="text-align:center; min-width: 110px;">
        <div class="artist-avatar" style="width:80px;height:80px;font-size:36px;margin-bottom:10px;">{{ artist.emoji }}</div>
        <div class="artist-name" style="font-size:15px;">{{ artist.name }}</div>
        <div class="artist-genre" style="margin-bottom:8px;">{{ artist.genre }}</div>
        <div class="artist-metric {% if artist.metric_color == 'blue' %}blue{% endif %}">{{ artist.metric }}</div>
      </div>
      <div>
        <div style="display:inline-block; font-size:10px; letter-spacing:2px; text-transform:uppercase; color:var(--text-dim); background:rgba(138,43,226,0.1); border:1px solid var(--border); border-radius:20px; padding:3px 12px; margin-bottom:14px;">{{ artist.service }}</div>
        <p style="font-size:14px; color:var(--text-muted); line-height:1.8;">{{ artist.story }}</p>
        <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary" style="margin-top:20px;font-size:11px;padding:9px 22px;">Get Same Results →</a>
      </div>
    </div>
    {% endfor %}
  </div>
</section>

<div class="neon-divider"></div>
<section class="cta-banner">
  <p class="cta-eyebrow">Your Turn</p>
  <h2 class="cta-title">Write Your Story.</h2>
  <p class="cta-subtitle">Every artist on this page started exactly where you are now. The only difference is they made the move.</p>
  <div class="cta-actions">
    <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary btn-lg">Start Today</a>
    <a href="{{ url_for('contact.contact') }}" class="btn btn-outline btn-lg">Ask a Question</a>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
pytest tests/test_main.py -v
```

Expected: `7 passed`

- [ ] **Step 8: Commit**

```bash
git add app/blueprints/main/routes.py app/templates/index.html app/templates/about.html app/templates/artists.html tests/test_main.py
git commit -m "feat: home, about, artists pages with neon urban design"
```

---

## Task 6: Services Blueprint

**Files:**
- Create: `app/blueprints/services/routes.py`
- Create: `app/templates/services.html`
- Create: `app/templates/services/promotion.html`
- Create: `app/templates/services/lessons.html`
- Create: `app/templates/services/production.html`
- Create: `tests/test_services.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_services.py

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
    assert b'your budget' in response.data.lower() or b'custom' in response.data.lower()

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
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_services.py -v
```

Expected: `FAILED` — routes don't exist yet.

- [ ] **Step 3: Create app/blueprints/services/routes.py**

```python
from flask import render_template
from . import services_bp

@services_bp.route('/')
def overview():
    return render_template('services.html')

@services_bp.route('/promotion')
def promotion():
    return render_template('services/promotion.html')

@services_bp.route('/lessons')
def lessons():
    return render_template('services/lessons.html')

@services_bp.route('/production')
def production():
    return render_template('services/production.html')
```

- [ ] **Step 4: Create app/templates/services.html**

```html
{% extends 'base.html' %}
{% block title %}Services{% endblock %}
{% block meta_description %}Professional music promotion, lessons, and artist production services by HALONEN FLOU.{% endblock %}

{% block content %}
<div class="page-header">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">What We Offer</p>
  <h1 class="page-title">Our Services</h1>
  <p class="page-subtitle">Three focused services designed to take artists from where they are to where they want to be.</p>
</div>

<section class="section">
  <div class="card-grid card-grid-3 container">

    <div class="card fade-in" style="display:flex;flex-direction:column;">
      <div class="card-icon">📢</div>
      <div class="card-title">Artist Promotion</div>
      <div class="card-body" style="flex:1;">Social media campaigns, playlist pitching, press coverage, PR strategies, and influencer outreach — all tailored to your unique sound and goals.</div>
      <div class="card-price" style="margin-top:20px;">You set your budget</div>
      <a href="{{ url_for('services.promotion') }}" class="btn btn-primary" style="margin-top:16px;">Explore Promotion</a>
    </div>

    <div class="card blue-accent fade-in" style="display:flex;flex-direction:column;">
      <div class="card-icon">🎸</div>
      <div class="card-title">Music Lessons</div>
      <div class="card-body" style="flex:1;">Private sessions in guitar, piano, voice, and music production. Learn from professionals who actively work in the industry, at your own pace.</div>
      <div class="card-price blue" style="margin-top:20px;">$100 / hour</div>
      <a href="{{ url_for('services.lessons') }}" class="btn btn-primary" style="margin-top:16px;">Explore Lessons</a>
    </div>

    <div class="card fade-in" style="display:flex;flex-direction:column;">
      <div class="card-icon">🎙️</div>
      <div class="card-title">Artist Production</div>
      <div class="card-body" style="flex:1;">Full-service production: studio recording, arrangement, mixing, mastering, and artist development. From idea to release-ready track.</div>
      <div class="card-price" style="margin-top:20px;">$2,500 / project</div>
      <a href="{{ url_for('services.production') }}" class="btn btn-primary" style="margin-top:16px;">Explore Production</a>
    </div>

  </div>
</section>

<div class="neon-divider"></div>
<section class="cta-banner">
  <p class="cta-eyebrow">Daily Subscription</p>
  <h2 class="cta-title">Start for $500/day</h2>
  <p class="cta-subtitle">Subscribe to our daily plan and get priority access to all services. Cancel anytime.</p>
  <div class="cta-actions">
    <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary btn-lg">Subscribe Now</a>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 5: Create app/templates/services/promotion.html**

```html
{% extends 'base.html' %}
{% block title %}Artist Promotion{% endblock %}
{% block meta_description %}Professional music artist promotion services — social media, PR, playlist pitching by HALONEN FLOU.{% endblock %}

{% block content %}
<div class="service-hero">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Service</p>
  <h1 class="page-title">📢 Artist Promotion</h1>
  <p class="page-subtitle">We amplify your music to the right audience through data-driven promotion strategies.</p>
  <div class="price-badge" style="margin-top:24px;">You Set Your Budget</div>
</div>

<section class="section">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:60px;max-width:900px;margin:0 auto;" class="fade-in">
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">What's Included</h3>
      <ul class="includes-list">
        <li>Instagram & TikTok content strategy</li>
        <li>Spotify playlist pitching (40+ curators)</li>
        <li>Press release writing & distribution</li>
        <li>Music blog outreach & features</li>
        <li>YouTube promotion & channel optimization</li>
        <li>Influencer & content creator collaboration</li>
        <li>Monthly analytics report</li>
        <li>Dedicated account manager</li>
      </ul>
    </div>
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">How Pricing Works</h3>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:16px;">Artist Promotion is fully flexible — you define your budget and we build a campaign around it. The more you invest, the wider the reach.</p>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:24px;">When you subscribe, you'll enter your daily promotion budget. Our team will immediately begin allocating it across the most effective channels for your genre and goals.</p>
      <a href="{{ url_for('subscriptions.subscribe') }}?service=promotion" class="btn btn-primary">Set My Budget →</a>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<section class="section section-alt">
  <h2 class="section-title">Frequently Asked Questions</h2>
  <div style="max-width:680px;margin:0 auto;">
    <div class="faq-item">
      <div class="faq-question">What is the minimum budget for promotion?</div>
      <div class="faq-answer">There is no strict minimum — you decide what you're comfortable investing. However, we recommend at least $50/day to see meaningful results across social and playlist channels within the first month.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">How quickly will I see results?</div>
      <div class="faq-answer">Most artists see measurable growth within 2–4 weeks. Playlist pitching typically yields results in 3–6 weeks, while social media campaigns can drive engagement within days.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Can I change my budget after subscribing?</div>
      <div class="faq-answer">Yes, you can adjust your daily budget at any time by contacting us. Changes take effect within 24 hours.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">What genres do you work with?</div>
      <div class="faq-answer">We work across all genres — R&B, Hip-Hop, Pop, Electronic, Rock, Indie, Country, Latin, and more. Our team includes specialists for each major genre.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Do you guarantee a certain number of streams or followers?</div>
      <div class="faq-answer">We do not guarantee specific numbers — anyone who does is selling fake engagement. We guarantee professional effort, transparent reporting, and real organic growth strategies.</div>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 6: Create app/templates/services/lessons.html**

```html
{% extends 'base.html' %}
{% block title %}Music Lessons{% endblock %}
{% block meta_description %}Private music lessons — guitar, piano, voice, and music production with professional instructors at HALONEN FLOU.{% endblock %}

{% block content %}
<div class="service-hero">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Service</p>
  <h1 class="page-title">🎸 Music Lessons</h1>
  <p class="page-subtitle">Learn from industry professionals. Private sessions tailored to your skill level and goals.</p>
  <div class="price-badge" style="margin-top:24px;">$100 / Hour</div>
</div>

<section class="section">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:60px;max-width:900px;margin:0 auto;" class="fade-in">
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">Instruments & Disciplines</h3>
      <ul class="includes-list">
        <li>Electric & Acoustic Guitar</li>
        <li>Piano & Keyboard</li>
        <li>Vocal Coaching & Technique</li>
        <li>Music Production (DAW: Ableton, FL Studio, Logic)</li>
        <li>Songwriting & Composition</li>
        <li>Music Theory & Ear Training</li>
        <li>Bass Guitar</li>
        <li>Drum Programming & Beatmaking</li>
      </ul>
    </div>
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">Session Details</h3>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:16px;">Sessions are 1-hour private lessons conducted via video call or in-person (New York area). Each session includes a personalized practice plan and lesson notes.</p>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:24px;">All skill levels welcome — from absolute beginners to advanced artists looking to refine specific techniques or add new skills to their repertoire.</p>
      <a href="{{ url_for('subscriptions.subscribe') }}?service=lessons" class="btn btn-primary">Book a Session →</a>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<section class="section section-alt">
  <h2 class="section-title">Frequently Asked Questions</h2>
  <div style="max-width:680px;margin:0 auto;">
    <div class="faq-item">
      <div class="faq-question">Do I need my own instrument?</div>
      <div class="faq-answer">For online sessions, yes — you'll need access to your instrument. For music production lessons, a laptop with a free DAW trial (Ableton, GarageBand, etc.) is sufficient to start.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Are sessions online or in-person?</div>
      <div class="faq-answer">Both options are available. Online sessions are conducted via Zoom or Google Meet. In-person sessions are available in the New York City area.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">How do I schedule a session?</div>
      <div class="faq-answer">After subscribing or booking, you'll receive a link to our scheduling system where you can choose available time slots with your assigned instructor.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Can I switch instruments or topics between sessions?</div>
      <div class="faq-answer">Yes. While we recommend consistency for fastest progress, you're free to explore different disciplines. Just let your instructor know in advance.</div>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 7: Create app/templates/services/production.html**

```html
{% extends 'base.html' %}
{% block title %}Artist Production{% endblock %}
{% block meta_description %}Full-service artist production — studio recording, mixing, mastering, and artist development by HALONEN FLOU.{% endblock %}

{% block content %}
<div class="service-hero">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Service</p>
  <h1 class="page-title">🎙️ Artist Production</h1>
  <p class="page-subtitle">From raw recordings to release-ready tracks. Complete production, mixing, and mastering.</p>
  <div class="price-badge" style="margin-top:24px;">$2,500 / Project</div>
</div>

<section class="section">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:60px;max-width:900px;margin:0 auto;" class="fade-in">
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">What's Included</h3>
      <ul class="includes-list">
        <li>Pre-production planning & arrangement</li>
        <li>Studio recording sessions (up to 3 tracks)</li>
        <li>Full mixing & mastering</li>
        <li>Instrument and vocal production</li>
        <li>Artist development coaching</li>
        <li>2 rounds of revisions included</li>
        <li>Final delivery in WAV + MP3 formats</li>
        <li>Distribution-ready masters</li>
      </ul>
    </div>
    <div>
      <h3 style="font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">Project Scope</h3>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:16px;">The $2,500 project fee covers a complete single or EP (up to 3 tracks) from pre-production through final masters. Larger projects (full albums, 4+ tracks) are quoted separately.</p>
      <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:24px;">Timeline: typically 4–6 weeks from kickoff to delivery, depending on project complexity and revision rounds.</p>
      <a href="{{ url_for('subscriptions.subscribe') }}?service=production" class="btn btn-primary">Start a Project →</a>
    </div>
  </div>
</section>

<div class="neon-divider"></div>

<section class="section section-alt">
  <h2 class="section-title">Frequently Asked Questions</h2>
  <div style="max-width:680px;margin:0 auto;">
    <div class="faq-item">
      <div class="faq-question">What do I need to bring to the project?</div>
      <div class="faq-answer">Just your ideas and any existing recordings or demos. We'll handle the rest — arrangement, production, session musicians if needed, mixing, and mastering.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">What if I need more than 3 tracks?</div>
      <div class="faq-answer">For projects exceeding 3 tracks, we provide a custom quote based on scope and complexity. Contact us to discuss your full vision before subscribing.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Do I own the masters?</div>
      <div class="faq-answer">Yes, 100%. You retain full ownership of all masters and recordings produced under this agreement. We retain no rights to your music.</div>
    </div>
    <div class="faq-item">
      <div class="faq-question">Can I combine production with promotion services?</div>
      <div class="faq-answer">Absolutely — and we recommend it. Many clients use our production service to create the music and then activate the promotion package for release. Contact us for combined service pricing.</div>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 8: Run tests — verify they pass**

```bash
pytest tests/test_services.py -v
```

Expected: `8 passed`

- [ ] **Step 9: Commit**

```bash
git add app/blueprints/services/routes.py app/templates/services.html app/templates/services/ tests/test_services.py
git commit -m "feat: services pages — overview, promotion, lessons, production with FAQ"
```

---

## Task 7: Contact Blueprint

**Files:**
- Create: `app/blueprints/contact/routes.py`
- Create: `app/templates/contact.html`
- Create: `tests/test_contact.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_contact.py

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
    assert b'message' in response.data.lower() or b'sent' in response.data.lower() or b'thank' in response.data.lower()

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
    assert b'required' in response.data.lower() or b'field' in response.data.lower()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_contact.py -v
```

Expected: `FAILED` — routes don't exist yet.

- [ ] **Step 3: Create app/blueprints/contact/routes.py**

```python
from flask import render_template, request, redirect, url_for, flash
from . import contact_bp
from app.extensions import db
from app.models import ContactMessage

@contact_bp.route('/', methods=['GET', 'POST'])
def contact():
    errors = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name:
            errors['name'] = 'This field is required.'
        if not email or '@' not in email:
            errors['email'] = 'A valid email address is required.'
        if not subject:
            errors['subject'] = 'This field is required.'
        if not message:
            errors['message'] = 'This field is required.'

        if not errors:
            msg = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('Your message has been sent! We\'ll get back to you within 24 hours.', 'success')
            return redirect(url_for('contact.contact'))

    return render_template('contact.html', errors=errors, form_data=request.form)
```

- [ ] **Step 4: Create app/templates/contact.html**

```html
{% extends 'base.html' %}
{% block title %}Contact{% endblock %}
{% block meta_description %}Contact HALONEN FLOU — reach Brent Halonen via email, phone, or our contact form.{% endblock %}

{% block content %}
<div class="page-header">
  <p class="section-eyebrow" style="text-align:left;margin-bottom:8px;">Get In Touch</p>
  <h1 class="page-title">Contact Us</h1>
  <p class="page-subtitle">Have a question? Want to discuss a project? We'd love to hear from you.</p>
</div>

<section class="section">
  <div class="contact-grid">

    <!-- Contact Info -->
    <div class="fade-in">
      <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:28px;">Direct Contact</h3>

      <div class="contact-info-item">
        <div class="contact-icon">📧</div>
        <div>
          <div style="font-size:11px;color:var(--primary);letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;">Email</div>
          <a href="mailto:bluealikeu@gmail.com" style="color:var(--text);">bluealikeu@gmail.com</a>
        </div>
      </div>

      <div class="contact-info-item">
        <div class="contact-icon">📞</div>
        <div>
          <div style="font-size:11px;color:var(--primary);letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;">Phone</div>
          <a href="tel:+19295039212" style="color:var(--text);">+1 (929) 503-9212</a>
        </div>
      </div>

      <div class="contact-info-item">
        <div class="contact-icon">📍</div>
        <div>
          <div style="font-size:11px;color:var(--primary);letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;">Location</div>
          <span>New York City, NY</span>
        </div>
      </div>

      <div class="contact-info-item">
        <div class="contact-icon">🕐</div>
        <div>
          <div style="font-size:11px;color:var(--primary);letter-spacing:2px;text-transform:uppercase;margin-bottom:2px;">Response Time</div>
          <span>Within 24 hours</span>
        </div>
      </div>

      <div style="margin-top:36px;padding:24px;background:rgba(138,43,226,0.06);border:1px solid var(--border);border-radius:12px;">
        <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Ready to Subscribe?</div>
        <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px;">Skip the form and go straight to choosing your service plan.</p>
        <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary" style="font-size:11px;padding:9px 20px;">View Plans →</a>
      </div>
    </div>

    <!-- Contact Form -->
    <div class="fade-in">
      <h3 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:28px;">Send a Message</h3>

      <form method="POST" action="{{ url_for('contact.contact') }}" novalidate>
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <div class="form-group">
          <label class="form-label" for="name">Your Name</label>
          <input type="text" id="name" name="name" class="form-control" placeholder="e.g. Nova Raines" value="{{ form_data.get('name', '') }}" required>
          {% if errors.get('name') %}<div class="form-error">{{ errors.name }}</div>{% endif %}
        </div>

        <div class="form-group">
          <label class="form-label" for="email">Email Address</label>
          <input type="email" id="email" name="email" class="form-control" placeholder="your@email.com" value="{{ form_data.get('email', '') }}" required>
          {% if errors.get('email') %}<div class="form-error">{{ errors.email }}</div>{% endif %}
        </div>

        <div class="form-group">
          <label class="form-label" for="subject">Subject</label>
          <input type="text" id="subject" name="subject" class="form-control" placeholder="e.g. Inquiry about promotion services" value="{{ form_data.get('subject', '') }}" required>
          {% if errors.get('subject') %}<div class="form-error">{{ errors.subject }}</div>{% endif %}
        </div>

        <div class="form-group">
          <label class="form-label" for="message">Message</label>
          <textarea id="message" name="message" class="form-control" placeholder="Tell us about your project, your goals, or any questions you have..." required>{{ form_data.get('message', '') }}</textarea>
          {% if errors.get('message') %}<div class="form-error">{{ errors.message }}</div>{% endif %}
        </div>

        <button type="submit" class="btn btn-primary btn-lg" style="width:100%;">Send Message →</button>
      </form>
    </div>

  </div>
</section>
{% endblock %}
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
pytest tests/test_contact.py -v
```

Expected: `6 passed`

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/contact/routes.py app/templates/contact.html tests/test_contact.py
git commit -m "feat: contact page with form, server-side validation, DB storage"
```

---

## Task 8: Subscriptions Blueprint (Payment-Ready Stub)

**Files:**
- Create: `app/blueprints/subscriptions/routes.py`
- Create: `app/templates/subscriptions/subscribe.html`
- Create: `app/templates/subscriptions/success.html`
- Create: `app/templates/subscriptions/cancel.html`
- Create: `tests/test_subscriptions.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_subscriptions.py

def test_subscribe_page_returns_200(client):
    response = client.get('/subscribe')
    assert response.status_code == 200

def test_subscribe_page_shows_all_services(client):
    response = client.get('/subscribe')
    assert b'promotion' in response.data.lower()
    assert b'lessons' in response.data.lower()
    assert b'production' in response.data.lower()

def test_subscribe_page_shows_daily_price(client):
    response = client.get('/subscribe')
    assert b'500' in response.data

def test_subscribe_post_saves_subscriber(client, db, app):
    with app.app_context():
        from app.models import Subscriber
        Subscriber.query.delete()
        db.session.commit()

    response = client.post('/subscribe', data={
        'name': 'Nova Raines',
        'email': 'nova@music.com',
        'service_type': 'promotion',
        'custom_amount': '200',
    }, follow_redirects=False)

    assert response.status_code in (302, 200)

    with app.app_context():
        from app.models import Subscriber
        sub = Subscriber.query.first()
        assert sub is not None
        assert sub.email == 'nova@music.com'
        assert sub.service_type == 'promotion'
        assert sub.status == 'pending'

def test_success_page_returns_200(client):
    response = client.get('/subscribe/success')
    assert response.status_code == 200

def test_cancel_page_returns_200(client):
    response = client.get('/subscribe/cancel')
    assert response.status_code == 200

def test_webhook_endpoint_exists(client):
    response = client.post('/subscribe/webhooks/helcim',
                           json={'event': 'payment.success'},
                           content_type='application/json')
    assert response.status_code in (200, 400, 501)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_subscriptions.py -v
```

Expected: `FAILED` — routes don't exist yet.

- [ ] **Step 3: Create app/blueprints/subscriptions/routes.py**

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

@subscriptions_bp.route('/', methods=['GET', 'POST'])
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

        if not errors:
            sub = Subscriber(
                name=name,
                email=email,
                service_type=service_type,
                custom_amount=float(custom_amount) if custom_amount else None,
            )
            db.session.add(sub)
            db.session.commit()
            # TODO: redirect to payment provider here (Helcim, Authorize.net, etc.)
            return redirect(url_for('subscriptions.success'))

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
    """
    Payment provider webhook handler — stub ready for integration.
    Supported providers: helcim, authorize, cashapp, quickbooks, melio, wave
    """
    allowed = {'helcim', 'authorize', 'cashapp', 'quickbooks', 'melio', 'wave'}
    if provider not in allowed:
        return jsonify({'error': 'Unknown provider'}), 400

    payload = request.get_json(silent=True) or {}
    # TODO: verify webhook signature per provider
    # TODO: update Subscriber.status based on event type
    # e.g. payload['event'] == 'payment.success' -> status = 'active'
    # e.g. payload['event'] == 'subscription.cancelled' -> status = 'cancelled'
    return jsonify({'received': True, 'provider': provider}), 200
```

- [ ] **Step 4: Create app/templates/subscriptions/subscribe.html**

```html
{% extends 'base.html' %}
{% block title %}Subscribe{% endblock %}
{% block meta_description %}Subscribe to HALONEN FLOU professional music services — daily subscription plan.{% endblock %}

{% block content %}
<div class="page-header" style="text-align:center;">
  <p class="section-eyebrow" style="text-align:center;margin-bottom:8px;">Get Started</p>
  <h1 class="page-title" style="text-align:center;">Choose Your Service</h1>
  <p class="page-subtitle" style="margin:0 auto;">Select a service, fill in your details, and we'll reach out within 24 hours to kick things off.</p>
</div>

<div class="subscribe-container">
  <div class="subscribe-card fade-in">

    <p style="font-size:11px;color:var(--primary);letter-spacing:3px;text-transform:uppercase;margin-bottom:20px;text-align:center;">Daily Plan · $500/day</p>

    {% if errors.get('service_type') %}
    <div class="flash-error">{{ errors.service_type }}</div>
    {% endif %}

    <form method="POST" action="{{ url_for('subscriptions.subscribe') }}" novalidate>
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

      <!-- Service selection -->
      <div class="form-group">
        <label class="form-label">Select Service</label>
        <div class="service-select-grid">
          {% for key, svc in services.items() %}
          <label class="service-option {% if (form_data.get('service_type') or preselect) == key %}selected{% endif %}">
            <input type="radio" name="service_type" value="{{ key }}" {% if (form_data.get('service_type') or preselect) == key %}checked{% endif %}>
            <div class="service-option-icon">{{ svc.emoji }}</div>
            <div class="service-option-name">{{ svc.name }}</div>
            <div class="service-option-price">{{ svc.price }}</div>
          </label>
          {% endfor %}
        </div>
      </div>

      <!-- Custom amount (promotion only) -->
      <div class="form-group" id="customPriceGroup" style="display:{% if (form_data.get('service_type') or preselect) == 'promotion' %}block{% else %}none{% endif %};">
        <label class="form-label" for="custom_amount">Your Daily Promotion Budget</label>
        <div class="price-input-wrapper">
          <input type="number" id="custom_amount" name="custom_amount" class="form-control" placeholder="e.g. 150" min="1" step="1" value="{{ form_data.get('custom_amount', '') }}">
        </div>
        <div style="font-size:11px;color:var(--text-dim);margin-top:4px;">Enter the daily amount you'd like to invest in promotion.</div>
      </div>

      <div class="form-group">
        <label class="form-label" for="sub_name">Full Name</label>
        <input type="text" id="sub_name" name="name" class="form-control" placeholder="Your name" value="{{ form_data.get('name', '') }}" required>
        {% if errors.get('name') %}<div class="form-error">{{ errors.name }}</div>{% endif %}
      </div>

      <div class="form-group">
        <label class="form-label" for="sub_email">Email Address</label>
        <input type="email" id="sub_email" name="email" class="form-control" placeholder="your@email.com" value="{{ form_data.get('email', '') }}" required>
        {% if errors.get('email') %}<div class="form-error">{{ errors.email }}</div>{% endif %}
      </div>

      <button type="submit" class="btn btn-primary btn-lg" style="width:100%;margin-top:8px;">Continue to Payment →</button>

      <p style="font-size:11px;color:var(--text-dim);text-align:center;margin-top:14px;">Payment processing coming soon. Your information is saved securely.</p>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Create app/templates/subscriptions/success.html**

```html
{% extends 'base.html' %}
{% block title %}You're In!{% endblock %}

{% block content %}
<section class="section" style="min-height:60vh;display:flex;align-items:center;justify-content:center;">
  <div style="text-align:center;max-width:480px;">
    <div style="font-size:64px;margin-bottom:24px;">🎉</div>
    <p style="font-size:10px;color:var(--primary);letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;">Subscription Confirmed</p>
    <h1 style="font-size:36px;font-weight:900;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">You're In!</h1>
    <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:32px;">Thank you for choosing HALONEN FLOU. We'll reach out within 24 hours to get everything set up and start working on your music career.</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a href="{{ url_for('main.artists') }}" class="btn btn-outline">See Artist Stories</a>
      <a href="{{ url_for('contact.contact') }}" class="btn btn-primary">Contact Us</a>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 6: Create app/templates/subscriptions/cancel.html**

```html
{% extends 'base.html' %}
{% block title %}Subscription Cancelled{% endblock %}

{% block content %}
<section class="section" style="min-height:60vh;display:flex;align-items:center;justify-content:center;">
  <div style="text-align:center;max-width:480px;">
    <div style="font-size:64px;margin-bottom:24px;">😔</div>
    <p style="font-size:10px;color:var(--text-muted);letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;">Subscription Cancelled</p>
    <h1 style="font-size:36px;font-weight:900;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">No Worries.</h1>
    <p style="font-size:14px;color:var(--text-muted);line-height:1.8;margin-bottom:32px;">Your subscription was cancelled. Whenever you're ready to start, we'll be here. Have questions? Reach out — we're happy to help you find the right plan.</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a href="{{ url_for('subscriptions.subscribe') }}" class="btn btn-primary">Try Again</a>
      <a href="{{ url_for('contact.contact') }}" class="btn btn-outline">Ask a Question</a>
    </div>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
pytest tests/test_subscriptions.py -v
```

Expected: `7 passed`

- [ ] **Step 8: Commit**

```bash
git add app/blueprints/subscriptions/routes.py app/templates/subscriptions/ tests/test_subscriptions.py
git commit -m "feat: subscription stub with service selection, custom pricing, webhook endpoints"
```

---

## Task 9: Full Test Run & Final Verification

**Files:** none — verification only

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (`28 passed` or similar).

- [ ] **Step 2: Start the app and verify all pages**

```bash
python run.py
```

Visit and verify each URL manually:
- http://localhost:5000 — Home page with hero, services, artists
- http://localhost:5000/about — About with bio, values, timeline
- http://localhost:5000/services — Services overview grid
- http://localhost:5000/services/promotion — Promotion detail + FAQ
- http://localhost:5000/services/lessons — Lessons detail + FAQ
- http://localhost:5000/services/production — Production detail + FAQ
- http://localhost:5000/artists — All 5 artist case studies
- http://localhost:5000/contact — Contact form
- http://localhost:5000/subscribe — Subscription form with service selector
- http://localhost:5000/subscribe/success — Success page
- http://localhost:5000/subscribe/cancel — Cancel page

- [ ] **Step 3: Test contact form end-to-end**

In the browser at http://localhost:5000/contact, fill in all fields and submit. Verify:
- Flash success message appears
- Page redirects back to /contact cleanly

- [ ] **Step 4: Test subscribe form end-to-end**

At http://localhost:5000/subscribe:
- Click "Artist Promotion" — custom budget input should appear
- Click "Music Lessons" — custom budget input should disappear
- Fill name + email, submit — should redirect to /subscribe/success

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: HALONEN FLOU complete website v1 — Flask, Neon Urban, 5 pages, contact form, subscription stubs"
```

---

## Payment Integration Notes (Future v2)

When ready to wire up payments, the integration points are:

1. **`app/blueprints/subscriptions/routes.py`** — `subscribe()` function, after `db.session.commit()`, add redirect to provider checkout URL
2. **`app/blueprints/subscriptions/routes.py`** — `webhook()` function, replace TODO comments with provider-specific signature verification and status updates
3. **`app/models.py`** — `Subscriber.provider_customer_id` field is ready to store the customer ID returned by any provider
4. Create `app/blueprints/subscriptions/providers/` directory with one module per provider (helcim.py, authorize.py, etc.)

Providers to integrate: **Helcim, Authorize.net, CashApp Pay, QuickBooks Payments, Melio, Wave**
