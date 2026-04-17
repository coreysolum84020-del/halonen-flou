from datetime import datetime, timezone
from sqlalchemy.orm import validates
from .extensions import db

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ContactMessage from {self.name}>'

class Subscriber(db.Model):
    __tablename__ = 'subscribers'

    VALID_SERVICE_TYPES = ('promotion', 'lessons', 'production')

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)  # no unique constraint: one email can subscribe to multiple services
    name = db.Column(db.String(120), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)
    plan_type = db.Column(db.String(20), default='daily')
    status = db.Column(db.String(20), default='pending')
    custom_amount = db.Column(db.Numeric(10, 2), nullable=True)   # for promotion service — client sets their own budget
    payment_provider = db.Column(db.String(50), nullable=True)    # e.g. helcim, authorize, cashapp, quickbooks, melio, wave
    provider_customer_id = db.Column(db.String(200), nullable=True)  # customer ID returned by payment provider
    wave_invoice_id = db.Column(db.String(200), nullable=True)   # Wave invoice ID for payment tracking
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @validates('service_type')
    def validate_service_type(self, key, value):
        if value not in self.VALID_SERVICE_TYPES:
            raise ValueError(f"service_type must be one of {self.VALID_SERVICE_TYPES}")
        return value

    def __repr__(self):
        return f'<Subscriber {self.name} ({self.service_type})>'

class AppConfig(db.Model):
    __tablename__ = 'app_config'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<AppConfig {self.key}>'
