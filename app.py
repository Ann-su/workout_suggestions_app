from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from Models.models import db, User, Workout
from agents import PersonalTrainer
from dotenv import load_dotenv
import json
import os
import markdown

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use your DB connection string here
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET")  # For session management and CSRF protection
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    # db.drop_all()
    db.create_all()


@app.route('/')
def index():
    session["user_id"] = None
    session["suggestion"] = None
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                flash('Logged in successfully!', category='success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match.', category='error')
            return render_template('register.html')

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        age = request.form['age']
        weight_kilograms = request.form['weight_kilograms']
        height_centimeters = request.form['height_centimeters']

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            new_user = User(first_name=first_name, last_name=last_name, email=email,
                            password_hash=generate_password_hash(password, method='scrypt'),
                            age=age, weight_kilograms=weight_kilograms, height_centimeters=height_centimeters)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', category='success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
    if not session.get("user_id", None):
        return redirect(url_for('home'))
    user = User.query.filter_by(id=session["user_id"]).first()
    from markupsafe import Markup

    suggestion_md = session.get("suggestion", "")
    suggestion_html = Markup(markdown.markdown(suggestion_md))
    return render_template("dashboard.html", suggestion=suggestion_html, user=user)


@app.route('/save_config', methods=['POST'])
def save_config():
    if not session.get("user_id", None):
        return redirect(url_for('home'))
    try:
        user = User.query.filter_by(id=session["user_id"]).first()
    except Exception as e:
        flash('Error updating user configuration: {}'.format(str(e)), category='error')
        return redirect(url_for('dashboard'))
    user.age = request.form['input_age']
    user.weight_kilograms = request.form['input_weight']
    user.height_centimeters = request.form['input_height']
    db.session.commit()
    flash('User configuration updated successfully!', category='success')
    return redirect(url_for('dashboard'))


@app.route('/process_workout', methods=['POST'])
def process_workout():
    if not session.get("user_id", None):
        return redirect(url_for('home'))
    text = request.form['input_workout']
    trainer = PersonalTrainer()
    try:
        result = trainer.workout_to_json(text)
        result = json.loads(result)["exercises"]
    except Exception as e:
        flash('Error processing workout: {}'.format(str(e)), category='error')
        return redirect(url_for('dashboard'))

    if "error" in result:
        flash('Error processing workout. Please try again.', category='error')
        return redirect(url_for('dashboard'))
    else:
        for exercise in result:
            new_workout = Workout(user_id=session["user_id"],
                                  exercise_name=exercise["exercise_name"],
                                  weight_kilograms=exercise["weight_kilograms"],
                                  repetitions=exercise["repetitions"],
                                  sets=exercise["sets"],
                                  distance_kilometers=exercise["distance_kilometers"],
                                  duration_minutes=exercise["duration_minutes"],
                                  kilocalories_burned=exercise["kilocalories_burned"])
            db.session.add(new_workout)
            db.session.commit()
        flash('Workout processed successfully!', category='success')

    if isinstance(result, (dict, list)):
        result = json.dumps(result)

    suggestion = trainer.suggest_workout(session["user_id"])

    session["suggestion"] = suggestion
    return redirect(url_for('dashboard'))


@app.route('/history')
def history():
    if not session.get("user_id", None):
        return redirect(url_for('home'))

    workouts = Workout.query.filter_by(user_id=session["user_id"]).all()

    return render_template("history.html", workouts=workouts)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get("user_id", None):
        return redirect(url_for('home'))
    user = User.query.filter_by(id=session["user_id"]).first()
    return render_template("settings.html", user=user)