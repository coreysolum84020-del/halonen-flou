from flask import render_template
from . import contact_bp

@contact_bp.route('/', methods=['GET', 'POST'])
def contact():
    return '<h1>Contact</h1>', 200
