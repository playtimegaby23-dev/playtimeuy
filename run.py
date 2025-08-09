import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
import pyrebase
from datetime import datetime
import firebase_admin

# 📂 Cargar variables de entorno
load_dotenv()

# 🚀 Inicializar Flask indicando dónde están los templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
app = Flask(__name__, template_folder=TEMPLATES_DIR)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# 🔐 Inicializar Firebase Admin SDK
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path or not os.path.isfile(cred_path):
    raise FileNotFoundError("❌ No se encontró el archivo de credenciales de Firebase Admin SDK.")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)

# 📦 Firestore
db = firestore.client()

# 🔑 Configuración Pyrebase
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": ""  # No usamos Realtime DB
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# 🏠 Página de inicio
@app.route('/')
def index():
    return render_template('index.html')

# 📝 Registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        tipo_cuenta = request.form.get('tipo_cuenta')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])

            user_id = user['localId']
            user_data = {
                "nombre": nombre,
                "email": email,
                "tipo_cuenta": tipo_cuenta,
                "fecha_registro": datetime.utcnow(),
                "verificado": False
            }
            db.collection('usuarios').document(user_id).set(user_data)

            flash("✅ Registro exitoso. Verifica tu correo electrónico.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                flash("❌ Este correo ya está registrado.", "danger")
            elif "WEAK_PASSWORD" in error_msg:
                flash("❌ Contraseña débil (mínimo 6 caracteres).", "danger")
            else:
                flash(f"❌ Error al registrar: {error_msg}", "danger")

    return render_template('register.html')

# 🔑 Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            info = auth.get_account_info(user['idToken'])

            if not info['users'][0]['emailVerified']:
                flash("❌ Verifica tu correo antes de iniciar sesión.", "warning")
                return redirect(url_for('login'))

            session['user'] = email
            return redirect(url_for('dashboard'))

        except Exception:
            flash("❌ Credenciales incorrectas.", "danger")

    return render_template('login.html')

# 📊 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

# 🚪 Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ▶️ Ejecutar aplicación
if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    )
