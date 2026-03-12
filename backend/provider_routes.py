from flask import Blueprint, jsonify, request
from models import db, Request
from auth_routes import token_required, role_required

provider_bp = Blueprint("provider", __name__, url_prefix="/api/provider")


@provider_bp.route("/requests", methods=["GET"])
@token_required
@role_required("provider")
def get_requests(current_user):

    requests = Request.query.all()

    result = []

    for r in requests:
        result.append({
            "id": r.id,
            "location_text": r.location_text,
            "issue_description": r.issue_description,
            "status": r.status,
            "provider_id": r.provider_id
        })

    return jsonify(result)


@provider_bp.route("/accept/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def accept_request(current_user, req_id):

    req = Request.query.get(req_id)

    if not req:
        return jsonify({"message": "Request not found"}), 404

    if req.status != "pending":
        return jsonify({"message": "Request already taken"}), 400

    req.status = "accepted"
    req.provider_id = current_user.id

    db.session.commit()

    return jsonify({"message": "Request accepted"})


@provider_bp.route("/update-status/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def update_status(current_user, req_id):

    req = Request.query.get(req_id)

    if not req:
        return jsonify({"message": "Request not found"}), 404

    data = request.json
    new_status = data.get("status")

    allowed = ["accepted", "in_progress", "completed"]

    if new_status not in allowed:
        return jsonify({"message": "Invalid status"}), 400

    req.status = new_status

    db.session.commit()

    return jsonify({"message": "Status updated"})