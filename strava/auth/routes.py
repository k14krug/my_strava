# auth/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from ..models import db, User
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.index"))

        flash("Invalid username or password", "danger")

    return render_template("auth/login.html", register_url=url_for("auth.register"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("auth.login"))
