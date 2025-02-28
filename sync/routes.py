# strava_app/sync/routes.py
from flask import Blueprint

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/manual_sync')
def manual_sync():
    return "Manual Sync Page (MVP placeholder)"
