from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    company_name = db.Column(db.String(120))


class Request(db.Model):
    __tablename__ = "request"

    id = db.Column(db.Integer, primary_key=True)

    location_text = db.Column(db.String(200))
    issue_description = db.Column(db.String(500))

    status = db.Column(db.String(50), default="pending")

    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    provider_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)