from flask import Blueprint, render_template
from flask_login import login_required
from mrp_engine import get_dashboard_stats, get_low_stock_alerts

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    stats = get_dashboard_stats()
    alerts = get_low_stock_alerts()
    return render_template('dashboard/index.html', stats=stats, alerts=alerts)
