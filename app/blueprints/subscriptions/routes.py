import traceback
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
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
        if payment_method not in ('wave', 'quickbooks'):
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
            if payment_method == 'quickbooks':
                card_number = request.form.get('card_number', '').strip()
                exp_month = request.form.get('card_exp_month', '').strip()
                exp_year = request.form.get('card_exp_year', '').strip()
                cvc = request.form.get('card_cvc', '').strip()

                if not card_number or not exp_month or not exp_year or not cvc:
                    errors['card'] = 'All card fields are required.'
                else:
                    from .providers.qbp import charge_card
                    try:
                        charge_id = charge_card(
                            name=name,
                            email=email,
                            service_type=service_type,
                            amount=amount,
                            card_number=card_number,
                            exp_month=exp_month,
                            exp_year=exp_year,
                            cvc=cvc,
                        )
                    except RuntimeError as e:
                        msg = str(e)
                        if 'declined' in msg.lower():
                            flash('Your card was declined. Please try a different card.', 'error')
                        else:
                            current_app.logger.error('QBP charge_card failed: %s\n%s', e, traceback.format_exc())
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
                        payment_provider='quickbooks',
                        provider_customer_id=charge_id,
                        status='active',
                    )
                    db.session.add(sub)
                    db.session.commit()
                    return redirect(url_for('subscriptions.success'))
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

        if errors:
            return render_template('subscriptions/subscribe.html',
                                   services=SERVICES,
                                   preselect=preselect,
                                   errors=errors,
                                   form_data=request.form)

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
    allowed = {'wave'}
    if provider not in allowed:
        return jsonify({'error': 'Unknown provider'}), 400

    if provider == 'wave':
        payload = request.get_json(silent=True) or {}
        from .providers.wave import handle_webhook
        handle_webhook(payload)

    return jsonify({'received': True, 'provider': provider}), 200
