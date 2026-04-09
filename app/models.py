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
    custom_amount = db.Column(db.Numeric(10, 2), nullable=True)
    payment_provider = db.Column(db.String(50), nullable=True)
    provider_customer_id = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscriber {self.name} ({self.service_type})>'
