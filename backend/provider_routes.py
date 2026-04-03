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
            "vehicle": r.vehicle,
            "status": r.status,
            "provider_id": r.provider_id,
            "price": r.price,
            "approx_price": r.approx_price,
            "last_quoted_by": r.last_quoted_by,
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
    try:
        initial_price = float(data.get("price"))
        # Use approx_price if available, or fallback to current record price
        approx_price = float(req.approx_price or req.price or 0)
    except (TypeError, ValueError):
        return jsonify({"message": "Initial quote price required and must be a number"}), 400
        
    # Constraint: Provider quote should not exceed approx_price + 500
    if initial_price > (approx_price + 500):
        return jsonify({"message": f"Your quote cannot exceed ₹{int(approx_price + 500)}"}), 400

    req.status = "negotiating"
    req.provider_id = current_user.id
    req.price = initial_price
    req.last_quoted_by = "provider"

    db.session.commit()

    return jsonify({"message": "Initial quote sent. Status: negotiating"})


@provider_bp.route("/negotiate/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def negotiate_request(current_user, req_id):
    req = Request.query.get(req_id)
    if not req:
        return jsonify({"message": "Request not found"}), 404
        
    if req.provider_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    action = data.get("action") # "accept" or "re-quote"

    if action == "accept":
        req.status = "accepted"
    elif action == "re-quote":
        try:
            new_price = float(data.get("price"))
            # Use approx_price if available, or fallback to current record price
            approx_price = float(req.approx_price or req.price or 0)
        except (TypeError, ValueError):
            return jsonify({"message": "Price required for re-quote and must be a number"}), 400
        
        # Constraint: Provider quote should not exceed approx_price + 500
        if new_price > (approx_price + 500):
            return jsonify({"message": f"Your quote cannot exceed ₹{int(approx_price + 500)}"}), 400
        
        req.price = new_price
        req.last_quoted_by = "provider"
        req.status = "negotiating"
    else:
        return jsonify({"message": "Invalid action"}), 400

    db.session.commit()
    return jsonify({"message": f"Request {action}ed successfuly"})


@provider_bp.route("/reject/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def reject_request(current_user, req_id):
    req = Request.query.get(req_id)
    if not req:
        return jsonify({"message": "Request not found"}), 404
        
    if req.provider_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    # Reset request to pending so other providers can see it
    req.status = "pending"
    req.provider_id = None
    req.price = req.approx_price
    req.last_quoted_by = "customer"

    db.session.commit()
    return jsonify({"message": "Request rejected and returned to pool"})


@provider_bp.route("/update-status/<int:req_id>", methods=["POST"])
@token_required
@role_required("provider")
def update_status(current_user, req_id):

    req = Request.query.get(req_id)

    if not req:
        return jsonify({"message": "Request not found"}), 404

    data = request.json
    new_status = data.get("status")

    allowed = ["accepted", "in_progress", "completed", "negotiating"]

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
            "approx_price": r.approx_price,
            "last_quoted_by": r.last_quoted_by,
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

    # Cumulative average rating from all rated completed jobs
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