from flask import Blueprint, jsonify, request
from models import db, Request
from auth_routes import token_required, role_required

customer_bp = Blueprint("customer", __name__, url_prefix="/api/customer")


@customer_bp.route("/requests", methods=["GET"])
@token_required
@role_required("customer")
def get_requests(current_user):

    requests = Request.query.filter_by(customer_id=current_user.id).all()

    result = []

    for r in requests:
        result.append({
            "id": r.id,
            "location_text": r.location_text,
            "issue_description": r.issue_description,
            "vehicle": r.vehicle,
            "status": r.status,
            "price": r.price,
            "rating": r.rating,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return jsonify(result)


@customer_bp.route("/requests", methods=["POST"])
@token_required
@role_required("customer")
def create_request(current_user):

    data = request.json

    req = Request(
        location_text=data.get("location_text"),
        issue_description=data.get("issue_description"),
        vehicle=data.get("vehicle"),
        approx_price=data.get("approx_price"),
        price=data.get("approx_price"), # Initial quote is the approx price
        last_quoted_by="customer",
        customer_id=current_user.id
    )

    db.session.add(req)
    db.session.commit()

    return jsonify({
        "message": "Request created",
        "request": {
            "id": req.id,
            "issue_description": req.issue_description,
            "location_text": req.location_text,
            "status": req.status,
            "price": req.price,
            "approx_price": req.approx_price,
            "rating": req.rating,
            "created_at": req.created_at.isoformat() if req.created_at else None
        }
    })


@customer_bp.route("/negotiate/<int:req_id>", methods=["POST"])
@token_required
@role_required("customer")
def negotiate_request(current_user, req_id):
    req = Request.query.filter_by(id=req_id, customer_id=current_user.id).first()
    if not req:
        return jsonify({"message": "Request not found"}), 404

    data = request.json
    action = data.get("action") # "accept" or "re-quote"

    if action == "accept":
        req.status = "accepted"
    elif action == "re-quote":
        new_price = data.get("price")
        if not new_price:
            return jsonify({"message": "Price required for re-quote"}), 400
        
        # Constraint: Customer quote should not go below approx_price - 500
        if new_price < (req.approx_price - 500):
            return jsonify({"message": f"Your quote cannot be below ₹{int(req.approx_price - 500)}"}), 400
        
        req.price = new_price
        req.last_quoted_by = "customer"
        req.status = "negotiating"
    else:
        return jsonify({"message": "Invalid action"}), 400

    db.session.commit()
    return jsonify({"message": f"Request {action}ed successfuly"})


@customer_bp.route("/requests/<int:req_id>/rate", methods=["POST"])
@token_required
@role_required("customer")
def rate_request(current_user, req_id):

    req = Request.query.filter_by(id=req_id, customer_id=current_user.id).first()

    if not req:
        return jsonify({"message": "Request not found"}), 404

    if req.status != "completed":
        return jsonify({"message": "Can only rate completed requests"}), 400

    data = request.json
    rating = data.get("rating")

    if not rating or rating < 1 or rating > 5:
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    req.rating = rating
    req.status = "reviewed"

    db.session.commit()

    return jsonify({"message": "Rating submitted"})