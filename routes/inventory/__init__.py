from flask import Blueprint

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

from . import suppliers, customers, materials, products, categories  # noqa: F401,E402
