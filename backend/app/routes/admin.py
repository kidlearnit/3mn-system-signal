from flask import Blueprint, request, jsonify
from ..db import SessionLocal, engine
admin_bp = Blueprint("admin", __name__)

# Dashboard routes are now handled by dashboard_api

@admin_bp.route("/healthz", methods=["GET"])
def healthz():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
