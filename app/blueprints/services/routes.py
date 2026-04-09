from flask import render_template
from . import services_bp

@services_bp.route('/')
def overview():
    return render_template('services.html')

@services_bp.route('/promotion')
def promotion():
    return '<h1>Promotion</h1>', 200

@services_bp.route('/lessons')
def lessons():
    return '<h1>Lessons</h1>', 200

@services_bp.route('/production')
def production():
    return '<h1>Production</h1>', 200
