# Importazione delle librerie necessarie
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import db
from blueprints.auth import auth_bp
from blueprints.home import home_bp
from blueprints.spotify import spotify_bp
from blueprints.compare import compare_bp

# Creazione dell'applicazione Flask
app = Flask(__name__)

# Impostazione della chiave segreta per gestire le sessioni
app.secret_key = 'your_secret_key'

# Configurazione del database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Inizializzazione del database
db.init_app(app)

# Inizializzazione di LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Registrazione dei blueprint
app.register_blueprint(compare_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(spotify_bp)

# Route principale per il login
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Funzione per caricare un utente
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Avvio dell'applicazione
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea le tabelle nel database
    app.run(debug=True)
