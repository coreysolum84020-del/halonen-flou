import re
from flask import render_template, request, redirect, url_for, flash
from . import contact_bp
from app.extensions import db
from app.models import ContactMessage

@contact_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
def contact():
    errors = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name:
            errors['name'] = 'This field is required.'
        if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors['email'] = 'A valid email address is required.'
        if not subject:
            errors['subject'] = 'This field is required.'
        if not message:
            errors['message'] = 'This field is required.'

        if not errors:
            msg = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            flash("Your message has been sent! We'll get back to you within 24 hours.", 'success')
            return redirect(url_for('contact.contact'))

    return render_template('contact.html', errors=errors, form_data=request.form)
