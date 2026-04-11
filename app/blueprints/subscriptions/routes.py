import uuid
from flask import render_template, request, redirect, url_for, flash, jsonify
from . import subscriptions_bp
from app.extensions import db, csrf
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
        payment_method = request.form.get('payment_method', 'wave')
        if payment_method not in ('wave', 'authorize'):
            payment_method = 'wave'

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
            if payment_method == 'authorize':
                from .providers.authnet import create_hosted_payment
                ref_id = str(uuid.uuid4())
                try:
                    checkout_url = create_hosted_payment(
                        name=name,
                        email=email,
                        service_type=service_type,
                        ref_id=ref_id,
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
                    payment_provider='authorize',
                    provider_customer_id=ref_id,
                )
                db.session.add(sub)
                db.session.commit()
                return redirect(checkout_url)
            else:
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
@csrf.exempt
def webhook(provider):
    """Payment provider webhook handler."""
    allowed = {'helcim', 'authorize', 'cashapp', 'quickbooks', 'melio', 'wave'}
    if provider not in allowed:
        return jsonify({'error': 'Unknown provider'}), 400

    if provider == 'wave':
        payload = request.get_json(silent=True) or {}
        from .providers.wave import handle_webhook
        handle_webhook(payload)
    elif provider == 'authorize':
        from .providers.authnet import handle_webhook
        # TODO: verify transaction against Authorize.net Transaction Details API
        # for now, configure IP allowlist in Authorize.net dashboard as mitigation
        handle_webhook(request.form.to_dict())

    return jsonify({'received': True, 'provider': provider}), 200
