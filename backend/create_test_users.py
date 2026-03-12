from app import create_app
from models import db, User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt()

with app.app_context():
    # Create Customer
    if not User.query.filter_by(email="customer@test.com").first():
        customer = User(
            name="John Customer",
            email="customer@test.com",
            password_hash=bcrypt.generate_password_hash("pass").decode(),
            role="customer"
        )
        db.session.add(customer)
    
    # Create Provider
    if not User.query.filter_by(email="provider@test.com").first():
        provider = User(
            name="Mike Provider",
            email="provider@test.com",
            password_hash=bcrypt.generate_password_hash("pass").decode(),
            role="provider",
            company_name="Mike's Repair Shop"
        )
        db.session.add(provider)
    
    db.session.commit()
    print("✅ Test users created!")