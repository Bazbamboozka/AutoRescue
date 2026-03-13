from flask import Blueprint, jsonify, request
from models import db, Request
from auth_routes import token_required, role_required

provider_bp = Blueprint("provider", __name__, url_prefix="/api/provider")


@provider_bp.route("/requests", methods=["GET"])
@token_required
@role_required("provider")
def get_requests(current_user):

    requests = Request.query.filter_by(status="pending").all()

    result = []

    for r in requests:
        result.append({
            "id": r.id,
            "location_text": r.location_text,
            "issue_description": r.issue_description,
            "status": r.status,
            "provider_id": r.provider_id,
            "price": r.price,
            "created_at": r.created_at.isoformat() if r.created_at else None
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

    data = request.json
    req.status = "accepted"
    req.provider_id = current_user.id
    req.price = data.get("price") if data else None

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

    if req.provider_id != current_user.id:
        return jsonify({"message": "Unauthorized — this is not your job"}), 403

    req.status = new_status

    db.session.commit()

    return jsonify({"message": "Status updated"})


@provider_bp.route("/my-jobs", methods=["GET"])
@token_required
@role_required("provider")
def get_my_jobs(current_user):

    jobs = Request.query.filter_by(provider_id=current_user.id).all()

    result = []

    for r in jobs:
        result.append({
            "id": r.id,
            "location_text": r.location_text,
            "issue_description": r.issue_description,
            "status": r.status,
            "price": r.price,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return jsonify(result)


@provider_bp.route("/earnings", methods=["GET"])
@token_required
@role_required("provider")
def get_earnings(current_user):

    jobs = Request.query.filter_by(
        provider_id=current_user.id,
        status="completed"
    ).all()

    total = sum(j.price for j in jobs if j.price)

    return jsonify({
        "total_earnings": total,
        "completed_jobs": len(jobs)
    })