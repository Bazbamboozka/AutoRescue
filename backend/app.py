from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from auth_routes import auth_bp
from admin_routes import admin_bp
from customer_routes import customer_bp
from provider_routes import provider_bp
import os


def create_app():
    app = Flask(__name__)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})


    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DATABASE_URL", "sqlite:///app.db"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "super-secret-key")

    # Initialize DB
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(customer_bp, url_prefix="/api/customer")
    app.register_blueprint(provider_bp, url_prefix="/api/provider")

    # Health check route
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # Create tables if not exist    
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        from models import User
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        
        admin = User.query.filter_by(email="admin@gmail.com").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@gmail.com",
                password_hash=bcrypt.generate_password_hash("admin123").decode(),
                role="admin",
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created")
        else:
            print("✅ Admin already exists")

    return app


# Create app instance for Gunicorn
app = create_app()


# Run locally
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)