from flask import render_template
from . import services_bp

@services_bp.route('/', strict_slashes=False)
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
