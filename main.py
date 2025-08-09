import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
import pyrebase
from datetime import datetime
import firebase_admin

# 🌐 Cargar variables de entorno desde .env
load_dotenv()

# 🚀 Inicializar Flask app
app = Flask(
    __name__,
    static_folder=os.path.join('app', 'static'),
    template_folder=os.path.join('app', 'templates')
)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# 🔐 Inicializar Firebase Admin SDK (para Firestore)
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path or not os.path.isfile(cred_path):
    raise FileNotFoundError("Credenciales de Firebase Admin no encontradas.")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)

# ☁️ Firestore (solo con Firebase Admin SDK)
db = firestore.client()

# 🔧 Pyrebase (para Auth)
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": ""  # No se usa Realtime DB
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# 🏠 Página principal (con video de fondo)
@app.route('/')
def index():
    return render_template('index.html', current_year=datetime.utcnow().year, show_video=True)

# 🔑 Registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        tipo_cuenta = request.form.get('tipo_cuenta')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            user_id = user['localId']
            db.collection('usuarios').document(user_id).set({
                "nombre": nombre,
                "email": email,
                "tipo_cuenta": tipo_cuenta,
                "fecha_registro": datetime.utcnow(),
                "verificado": False
            })
            flash("Registro exitoso. Verifica tu correo electrónico antes de iniciar sesión.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                flash("Este correo ya está registrado.", "danger")
            elif "WEAK_PASSWORD" in error_msg:
                flash("La contraseña es muy débil (mínimo 6 caracteres).", "danger")
            else:
                flash("Ocurrió un error al registrar. Verifica los datos.", "danger")

    return render_template('register.html', show_video=False)

# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            info = auth.get_account_info(user['idToken'])

            if not info['users'][0]['emailVerified']:
                flash("Verifica tu correo antes de iniciar sesión.", "warning")
                return redirect(url_for('login'))

            session['user'] = email
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for('dashboard'))
        except Exception:
            flash("Credenciales incorrectas o error al iniciar sesión.", "danger")

    return render_template('login.html', show_video=False)

# 📊 Dashboard (panel privado)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Inicia sesión para acceder al panel.", "warning")
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=session['user'])

# 🔓 Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Sesión cerrada exitosamente.", "info")
    return redirect(url_for('login'))

# ❌ Página 404 personalizada
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# ▶️ Ejecutar servidor
if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )
