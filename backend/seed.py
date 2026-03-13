from app import create_app
from models import db, User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt()

with app.app_context():

    if not User.query.filter_by(email="admin@auto.com").first():

        admin = User(
            name="Admin",
            email="admin@auto.com",
            password_hash=bcrypt.generate_password_hash("admin123").decode(),
            role="admin",
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully.")