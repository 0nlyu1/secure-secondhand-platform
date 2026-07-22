from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(30), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    bio = db.Column(db.String(300), default="")

    points = db.Column(db.Integer, default=10000)

    is_admin = db.Column(db.Boolean, default=False)

    is_suspended = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text, nullable=False)

    price = db.Column(db.Integer, nullable=False)

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    is_blocked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    content = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reporter_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    target_type = db.Column(db.String(20))

    target_id = db.Column(db.Integer)

    reason = db.Column(db.Text)

    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    amount = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)