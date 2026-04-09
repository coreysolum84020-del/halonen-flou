from flask import Blueprint
subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/subscribe')
from . import routes  # noqa: F401, E402
