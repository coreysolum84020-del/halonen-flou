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

        if not errors:
            amount = None
            if custom_amount:
                try:
                    amount = float(custom_amount)
                    if amount <= 0:
                        errors['custom_amount'] = 'Budget must be a positive number.'
                except ValueError:
                    errors['custom_amount'] = 'Budget must be a valid number.'

        if not errors:
            sub = Subscriber(
                name=name,
                email=email,
                service_type=service_type,
                custom_amount=amount,
            )
            db.session.add(sub)
            db.session.commit()
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
