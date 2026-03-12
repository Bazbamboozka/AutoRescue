from flask import Blueprint, jsonify
from models import User, Request
from auth_routes import token_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/users", methods=["GET"])
@token_required
@role_required("admin")
def get_users(current_user):

    users = User.query.all()

    result = []

    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        })

    return jsonify(result)


@admin_bp.route("/requests", methods=["GET"])
@token_required
@role_required("admin")
def get_requests(current_user):

    requests = Request.query.all()

    result = []

    for r in requests:
        result.append({
            "id": r.id,
            "issue_description": r.issue_description,
            "location_text": r.location_text,
            "status": r.status
        })

    return jsonify(result)