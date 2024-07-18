from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://username:password@localhost/db"
app.config["SECRET_KEY"] = "secret_key_here"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    contact = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    creator = db.relationship("User", backref="events")

class EventCreator(db.Model):
    __tablename__ = "event_creators"
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    event = db.relationship("Event", backref="creators")
    user = db.relationship("User", backref="created_events")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        flash("Invalid email or password")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        contact = request.form["contact"]
        phone_number = request.form["phone_number"]
        password = generate_password_hash(request.form["password"])
        user = User(name=name, email=email, contact=contact, phone_number=phone_number, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/home")
@login_required
def home():
    events = Event.query.order_by(db.func.rand()).limit(10)
    return render_template("home.html", events=events)

@app.route("/event/<int:event_id>")
@login_required
def event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("event.html", event=event)

@app.route("/profile")
@login_required
def profile():
    user = current_user
    events = user.events
    return render_template("profile.html", user=user, events=events)

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        location = request.form["location"]
        description = request.form["description"]
        event = Event(title=title, date=date, location=location, description=description, created_by=current_user.id)
        db.session.add(event)
        db.session.commit()
        flash("Event created successfully")
        return redirect(url_for("home"))
    return render_template("create_event.html")

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for("home"))
    events = Event.query.all()
    users = User.query.all()
    return render_template("admin_dashboard.html", events=events, users=users)

@app.route("/admin_events", methods=["GET", "POST"])
@login_required
def admin_events():
    if not current_user.is_admin:
        return redirect(url_for("home"))
    if request.method == "POST":
        event_id = request.form["event_id"]
        event = Event.query.get_or_404(event_id)
        if request.form["action"] == "edit":
            event.title = request.form["title"]
            event.date = request.form["date"]
           