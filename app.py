import os
import io
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///collegeevents.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    isadmin = db.Column(db.Boolean, default=False)
    # Admin
    name = db.Column(db.String(100))
    staffid = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    department = db.Column(db.String(50))
    years_experience = db.Column(db.Integer)
    # Student
    rollno = db.Column(db.String(20))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    batch = db.Column(db.String(10))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    theme = db.Column(db.String(80))
    logo = db.Column(db.String(120))
    event_type = db.Column(db.String(20)) # intracollege/intercollege
    start_date = db.Column(db.String(20))
    num_days = db.Column(db.Integer)
    students_allowed = db.Column(db.Integer)
    volunteers_required = db.Column(db.Integer)
    num_sub_events = db.Column(db.Integer)
    spectators_allowed = db.Column(db.Integer)
    volunteers_allowed_per_event = db.Column(db.Integer)
    createdby = db.Column(db.Integer, db.ForeignKey('user.id'))

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    eventid = db.Column(db.Integer, db.ForeignKey('event.id'))
    role = db.Column(db.String(16), default="participant") # participant/volunteer
    qrtoken = db.Column(db.String(100), unique=True)
    checkedin = db.Column(db.Boolean, default=False)
    used = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('choose_role.html')

@app.route('/choose_role', methods=['GET', 'POST'])
def choose_role():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'admin':
            return redirect(url_for('register_admin'))
        elif role == 'student':
            return redirect(url_for('register_student'))
    return render_template('choose_role.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'admin' if user.isadmin else 'student'
            return redirect(url_for('dashboard'))
        flash("Invalid username or password")
    return render_template('login.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        data = request.form
        if User.query.filter_by(username=data['username']).first():
            flash('Username already exists!')
            return redirect(url_for('register_admin'))
        user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            isadmin=True,
            name=data['name'],
            staffid=data['staffid'],
            dob=data['dob'],
            department=data['department'],
            years_experience=data['years_experience']
        )
        db.session.add(user)
        db.session.commit()
        flash('Admin registered! Please login.')
        return redirect(url_for('login'))
    return render_template('register_admin.html')

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        data = request.form
        if User.query.filter_by(username=data['username']).first():
            flash('Username already exists!')
            return redirect(url_for('register_student'))
        user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            isadmin=False,
            name=data['name'],
            rollno=data['rollno'],
            email=data['email'],
            phone=data['phone'],
            department=data['department'],
            branch=data['branch'],
            batch=data['batch'],
            dob=data['dob']
        )
        db.session.add(user)
        db.session.commit()
        flash('Student registered! Please login.')
        return redirect(url_for('login'))
    return render_template('register_student.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    events = Event.query.all()
    registrations = Registration.query.filter_by(userid=user.id).all()
    # Leaderboards
    participation_leaders = db.session.query(
        User, db.func.count(Registration.id).label('events_count')
    ).join(Registration, Registration.userid == User.id).group_by(User.id).order_by(db.desc('events_count')).limit(5).all()
    volunteer_leaders = db.session.query(
        User, db.func.count(Registration.id).label('volunteer_count')
    ).filter(Registration.role=="volunteer").join(Registration, Registration.userid == User.id).group_by(User.id).order_by(db.desc('volunteer_count')).limit(5).all()
    return render_template('dashboard.html', user=user, events=events, registrations=registrations,
                           participation_leaders=participation_leaders, volunteer_leaders=volunteer_leaders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Inbox route
@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.timestamp.desc()).all()
    return render_template('inbox.html', messages=messages)

# Add other routes: settings, admin_events, access_students, etc.

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
