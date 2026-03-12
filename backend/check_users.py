from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    users = User.query.all()
    print("\n=== ALL USERS IN DATABASE ===")
    for u in users:
        print(f"Email: {u.email} | Role: {u.role}")
    print("=" * 35)
    