from flask import render_template, jsonify
from . import subscriptions_bp
from app.extensions import csrf

SERVICES = {
    'lessons':    {'name': 'Music Lessons',    'emoji': '🎸', 'price': '$150 – $250'},
    'promotion':  {'name': 'Artist Promotion', 'emoji': '📢', 'price': '$400'},
    'production': {'name': 'Artist Production','emoji': '🎙️', 'price': '$650'},
}

QBP_LINKS = {
    'production': 'https://connect.intuit.com/portal/app/CommerceNetwork/view/scs-v1-79a25230f28349379adc6ef8ad8e7dae6812a5a814ef43e7a16aefc06f8cec0544ab77f2161a484d8b9eb2f971c605cc?locale=EN_US&cta=paylinkbuybutton',
    'promotion':  'https://connect.intuit.com/portal/app/CommerceNetwork/view/scs-v1-4c41727a06e34628b6c7ca55c2afa5beeb2f5d27fda749338b4e52ef7e30fbf1d4a0a4e7b07e48a9a1a34d90cc3df56c?locale=EN_US&cta=paylinkbuybutton',
    'lessons_250':'https://connect.intuit.com/portal/app/CommerceNetwork/view/scs-v1-ff2da355b23d4749868e8743fff7cc107c6aee2488ff46eaade4ea5411cfd19de6f39c554f2d44d9b8adb2e240582322?locale=EN_US&cta=paylinkbuybutton',
    'lessons_150':'https://connect.intuit.com/portal/app/CommerceNetwork/view/scs-v1-d29e72474d794c7b84d581d4625175cb4c1d8300e6884a4683d7f7a78f52ceabd5f364502f224d1986e0b0414a1a1788?locale=EN_US&cta=paylinkbuybutton',
}


@subscriptions_bp.route('/', strict_slashes=False)
def subscribe():
    return render_template('subscriptions/subscribe.html',
                           services=SERVICES,
                           qbp_links=QBP_LINKS)


@subscriptions_bp.route('/success')
def success():
    return render_template('subscriptions/success.html')


@subscriptions_bp.route('/cancel')
def cancel():
    return render_template('subscriptions/cancel.html')


@subscriptions_bp.route('/webhooks/<provider>', methods=['POST'])
@csrf.exempt
def webhook(provider):
    return jsonify({'received': True, 'provider': provider}), 200
