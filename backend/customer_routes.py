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
            "status": r.status
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
        customer_id=current_user.id
    )

    db.session.add(req)
    db.session.commit()

    return jsonify({"message": "Request created"})