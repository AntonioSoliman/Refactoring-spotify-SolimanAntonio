from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import re  # Importiamo il modulo per le regular expressions

auth_bp = Blueprint('auth', __name__)

def is_valid_username(username):
    # Controlla che l'username abbia almeno 4 caratteri
    if len(username) < 4:
        return False, "L'username deve contenere almeno 4 caratteri"
    
    # Controlla che l'username contenga solo caratteri alfanumerici
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False, "L'username può contenere solo lettere, numeri e underscore"
    
    return True, ""

def is_valid_password(password):
    # Controlla che la password abbia almeno 6 caratteri
    if len(password) < 6:
        return False, "La password deve contenere almeno 6 caratteri"
    return True, ""

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validazione username
        valid_username, username_error = is_valid_username(username)
        if not valid_username:
            return render_template('register.html', error=username_error)
        
        # Validazione password
        valid_password, password_error = is_valid_password(password)
        if not valid_password:
            return render_template('register.html', error=password_error)
        
        # Controllo se l'username esiste già
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Questo username è già in uso.")

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)  
            return redirect(url_for('home.home'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f"Errore durante la registrazione: {e}")
    
    return render_template('register.html', error=None)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home.home'))

        return render_template('login.html', error="Credenziali non valide.")
    return render_template('login.html', error=None)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))