from flask import render_template
from . import subscriptions_bp

@subscriptions_bp.route('/')
def subscribe():
    return '<h1>Subscribe</h1>', 200

@subscriptions_bp.route('/success')
def success():
    return '<h1>Success</h1>', 200

@subscriptions_bp.route('/cancel')
def cancel():
    return '<h1>Cancel</h1>', 200
