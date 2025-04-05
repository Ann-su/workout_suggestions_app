from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150),  nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    weight_kilograms = db.Column(db.Integer, nullable=True)
    height_centimeters = db.Column(db.Integer, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    intensity = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Method to set password using hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_name = db.Column(db.String(150),  nullable=False)
    weight_kilograms = db.Column(db.Integer, nullable=True)
    repetitions = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    distance_kilometers = db.Column(db.Integer, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    kilocalories_burned = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'exercise_name': self.exercise_name,
            'weight_kilograms': self.weight_kilograms,
            'repetitions': self.repetitions,
            'sets': self.sets,
            'distance_kilometers': self.distance_kilometers,
            'duration_minutes': self.duration_minutes,
            'kilocalories_burned': self.kilocalories_burned,
            'created_at': self.created_at.isoformat()
        }