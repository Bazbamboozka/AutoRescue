from flask import Blueprint, jsonify, request
from models import db, Request
from auth_routes import token_required, role_required

provider_bp = Blueprint("provider", __name__, url_prefix="/api/provider")


@provider_bp.route("/requests", methods=["GET"])
@token_required
@role_required("provider")
def get_available_requests(current_user):

    # For simplicity, returning all pending requests
    requests = Request.query.filter_by(status="pending").all()

    result = []
    for r in requests:
        result.append({
            "id": r.id,
            "location_text": r.location_text,
            "issue_description": r.issue_description,
            "vehicle": getattr(r, "vehicle", None),
            "approx_price": r.approx_price
        })

    return jsonify(result)


@provider_bp.route("/accept/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def accept_request(current_user, req_id):

    req = Request.query.get(req_id)
    if not req:
        return jsonify({"message": "Request not found"}), 404

    data = request.json
    price = data.get("price")

    if not price:
        return jsonify({"message": "Price is required"}), 400

    # Minimum system validation: quote must be within range of approx_price
    if price > (req.approx_price + 500):
        return jsonify({"message": f"Quote too high. Maximum allowed is {req.approx_price + 500}"}), 400

    req.provider_id = current_user.id
    req.status = "negotiating" # Set to negotiating first
    req.price = price
    req.last_quoted_by = "provider"

    db.session.commit()

    return jsonify({"message": "Quote sent to customer"})


@provider_bp.route("/negotiate/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def negotiate(current_user, req_id):

    req = Request.query.get(req_id)
    data = request.json
    action = data.get("action") # "accept" or "re-quote"

    if action == "accept":
        req.status = "accepted"
    else:
        req.price = data.get("price")
        req.last_quoted_by = "provider"
        req.status = "negotiating"

    db.session.commit()
    return jsonify({"message": "Negotiation updated"})


@provider_bp.route("/reject/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def reject_request(current_user, req_id):

    req = Request.query.get(req_id)
    if not req: return jsonify({"message":"Not found"}), 404

    req.provider_id = None
    req.status = "pending"
    db.session.commit()
    return jsonify({"message": "Job rejected"})


@provider_bp.route("/update-status/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def update_status(current_user, req_id):

    req = Request.query.get(req_id)
    if not req:
        return jsonify({"message": "Request not found"}), 404

    data = request.json
    new_status = data.get("status")

    if new_status:
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
            "approx_price": r.approx_price,
            "last_quoted_by": r.last_quoted_by,
            "rating": r.rating,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return jsonify(result)


@provider_bp.route("/earnings", methods=["GET"])
@token_required
@role_required("provider")
def get_earnings(current_user):

    # Filter for jobs that generate revenue (completed or reviewed)
    jobs = Request.query.filter(
        Request.provider_id == current_user.id,
        Request.status.in_(["completed", "reviewed"])
    ).all()

    total = sum(j.price for j in jobs if j.price)

    # Cumulative average rating from all rated jobs
    rated_jobs = [j for j in jobs if j.rating is not None]
    avg_rating = round(sum(j.rating for j in rated_jobs) / len(rated_jobs), 2) if rated_jobs else None

    # Per-job breakdown for chart (price + created_at)
    job_breakdown = [
        {
            "id": j.id,
            "price": j.price or 0,
            "rating": j.rating,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "issue_description": j.issue_description
        }
        for j in jobs
    ]

    return jsonify({
        "total_earnings": total,
        "completed_jobs": len(jobs),
        "average_rating": avg_rating,
        "rated_jobs": len(rated_jobs),
        "job_breakdown": job_breakdown
    })