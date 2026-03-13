from flask import Blueprint, request, jsonify, current_app
from models import db, User
from flask_bcrypt import Bcrypt
import jwt
import datetime
from functools import wraps

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

def generate_token(user):
    return jwt.encode(
        {
            "id": user.id,
            "role": user.role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")

        if not auth:
            return jsonify({"message": "Token missing"}), 401

        token = auth.split(" ")[1]

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user = User.query.get(data["id"])
        except:
            return jsonify({"message": "Invalid token"}), 401

        return f(user, *args, **kwargs)

    return decorated


def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(user, *args, **kwargs):
            if user.role != role:
                return jsonify({"message": "Unauthorized"}), 403

            return f(user, *args, **kwargs)

        return decorated

    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    if data.get("role") == "admin":
        return jsonify({"message": "Cannot self-register as admin"}), 403

    password_hash = bcrypt.generate_password_hash(data["password"]).decode()

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=password_hash,
        role=data["role"]
    )

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    })


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"message": "Account is banned"}), 403

    if not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    token = generate_token(user)

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    })


@auth_bp.route("/me")
@token_required
def me(user):
    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    })