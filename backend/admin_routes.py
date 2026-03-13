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
            "role": u.role,
            "is_active": u.is_active
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
            "status": r.status,
            "price": r.price,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "rating": r.rating
        })

    return jsonify(result)

    @admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@role_required("admin")
def delete_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    from models import db
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@token_required
@role_required("admin")
def toggle_user_status(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    user.is_active = not user.is_active
    from models import db
    db.session.commit()
    return jsonify({"message": "Status updated", "is_active": user.is_active})