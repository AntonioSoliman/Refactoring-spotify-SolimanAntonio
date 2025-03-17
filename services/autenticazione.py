from flask import render_template, request, redirect, url_for,session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from services.spotify_oauth import search_playlists, get_random_playlists

def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Questo username è già in uso.")

        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user) 
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f"Errore durante la registrazione: {e}")
    return render_template('register.html', error=None)

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))

        return render_template('login.html', error="Credenziali non valide.")
    return render_template('login.html', error=None)

@login_required
def home():
    query = request.args.get("query")
    playlists = search_playlists(query) if query else get_random_playlists()
    return render_template(
        "home.html",
        username=current_user.username,
        playlists=playlists
    )

@login_required
def logout():

    session.pop("token_info", None)
    logout_user()
    return redirect(url_for("login"))