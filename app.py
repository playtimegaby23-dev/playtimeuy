import os
import json
import uuid
from pathlib import Path
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory, abort
)
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import TemplateNotFound

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Definir rutas base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Determinar carpeta de templates y static automáticamente (soporta estructura /app/templates)
if (BASE_DIR / "templates").exists():
    templates_path = BASE_DIR / "templates"
elif (BASE_DIR / "app" / "templates").exists():
    templates_path = BASE_DIR / "app" / "templates"
else:
    # fallback: crear carpeta "templates" para evitar errores
    templates_path = BASE_DIR / "templates"
    templates_path.mkdir(parents=True, exist_ok=True)

if (BASE_DIR / "static").exists():
    static_path = BASE_DIR / "static"
elif (BASE_DIR / "app" / "static").exists():
    static_path = BASE_DIR / "app" / "static"
else:
    static_path = BASE_DIR / "static"
    static_path.mkdir(parents=True, exist_ok=True)

# Inicializar Flask con rutas explícitas para static y templates
app = Flask(
    __name__,
    static_folder=str(static_path),
    template_folder=str(templates_path)
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-this")

# Inicialización opcional Firebase Admin SDK
FIREBASE_ADMIN_AVAILABLE = False
AUTH_AVAILABLE = False
USE_FIRESTORE = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        FIREBASE_ADMIN_AVAILABLE = True
        USE_FIRESTORE = True
    else:
        print("No se encontró GOOGLE_APPLICATION_CREDENTIALS o la ruta no existe. Usando modo local (sin Firestore).")
except Exception as e:
    print("Firebase Admin no disponible o falló inicialización:", e)

# Inicialización opcional Pyrebase para auth
try:
    import pyrebase

    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.getenv("FIREBASE_APP_ID", ""),
    }

    if firebase_config["apiKey"]:
        firebase = pyrebase.initialize_app(firebase_config)
        auth = firebase.auth()
        AUTH_AVAILABLE = True
    else:
        print("Pyrebase configurado incompleto: no se activará auth remota.")
except Exception as e:
    print("Pyrebase no disponible:", e)

# Backend local: archivo JSON para usuarios
USERS_FILE = DATA_DIR / "users.json"
if not USERS_FILE.exists():
    USERS_FILE.write_text(json.dumps({}))


def load_users():
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {}


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False))


def create_local_user(email, password, username="", full_name=""):
    users = load_users()
    if email in users:
        raise ValueError("El email ya está registrado (local).")
    local_id = str(uuid.uuid4())
    users[email] = {
        "localId": local_id,
        "email": email,
        "password_hash": generate_password_hash(password),
        "username": username or email.split("@")[0],
        "full_name": full_name,
        "emailVerified": False,
        "role": "buyer",
        "is_admin": False
    }
    save_users(users)
    return users[email]


def authenticate_local_user(email, password):
    users = load_users()
    user = users.get(email)
    if not user:
        raise ValueError("Usuario no encontrado (local).")
    if not check_password_hash(user["password_hash"], password):
        raise ValueError("Contraseña incorrecta (local).")
    return user

# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# Decorador para cargar datos del usuario en sesión
def load_user_data(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' in session:
            uid = session['user']
            if USE_FIRESTORE and db is not None:
                try:
                    doc = db.collection("usuarios").document(uid).get()
                    if doc.exists:
                        d = doc.to_dict()
                        session['role'] = d.get('role', 'buyer')
                        session['is_admin'] = d.get('is_admin', False)
                    else:
                        session.clear()
                        flash("Usuario no encontrado. Inicia sesión nuevamente.", "danger")
                        return redirect(url_for('login'))
                except Exception as e:
                    print("Error load_user_data firestore:", e)
                    session['role'] = 'buyer'
                    session['is_admin'] = False
            else:
                users = load_users()
                found = None
                for email, u in users.items():
                    if u.get("localId") == uid:
                        found = u
                        break
                if not found:
                    session.clear()
                    flash("Usuario no encontrado (local). Inicia sesión nuevamente.", "danger")
                    return redirect(url_for('login'))
                session['role'] = found.get('role', 'buyer')
                session['is_admin'] = found.get('is_admin', False)
        return f(*args, **kwargs)
    return decorated

# Rutas principales
@app.route("/")
def index():
    video_path = Path(app.static_folder) / "video" / "banner.mp4"
    img_path = Path(app.static_folder) / "img" / "banner.png"
    has_video = video_path.exists()
    has_img = img_path.exists()
    try:
        return render_template("index.html", show_video=has_video, has_img=has_img)
    except TemplateNotFound:
        # Mensaje claro si faltan templates
        return ("Plantilla index.html no encontrada en: %s" % app.template_folder), 500


@app.route("/debug-static/<path:filename>")
def debug_static(filename):
    return send_from_directory(app.static_folder, filename)


@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        username = request.form.get("username") or (email.split("@")[0] if email else "")
        full_name = request.form.get("full_name", "")

        if not email or not password:
            flash("Email y contraseña requeridos.", "danger")
            return redirect(url_for("register"))

        # Auth remota
        if AUTH_AVAILABLE:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                local_id = user.get('localId') or user.get('local_id') or str(uuid.uuid4())
                if USE_FIRESTORE and db is not None:
                    db.collection("usuarios").document(local_id).set({
                        "full_name": full_name,
                        "username": username,
                        "email": email,
                        "role": "buyer",
                        "registered_at": firestore.SERVER_TIMESTAMP,
                        "verified": False,
                        "auth_provider": "password",
                        "is_admin": False
                    })
                flash("Registro exitoso. Revisa tu correo para verificar la cuenta (si aplica).", "success")
                return redirect(url_for("login"))
            except Exception as e:
                print("Error registro remoto:", e)
                flash("No se pudo registrar en auth remota, intentando registro local.", "warning")

        # Fallback local
        try:
            create_local_user(email, password, username, full_name)
            flash("Registro local exitoso. Ya podés iniciar sesión.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            print("Error registro local:", e)
            flash(str(e), "danger")

    try:
        return render_template("register.html")
    except TemplateNotFound:
        return ("Plantilla register.html no encontrada en: %s" % app.template_folder), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email y contraseña requeridos.", "danger")
            return redirect(url_for("login"))

        # Auth remota
        if AUTH_AVAILABLE:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                local_id = user.get('localId')
                session['user'] = local_id
                session['email'] = email
                flash("Bienvenido/a (auth remota).", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                print("Error login remoto:", e)
                flash("No se pudo iniciar sesión en el servicio remoto. Intentando login local.", "warning")

        # Fallback local
        try:
            user = authenticate_local_user(email, password)
            session['user'] = user["localId"]
            session['email'] = user["email"]
            verified_msg = "Tu correo no está verificado (modo local)." if not user.get("emailVerified") else ""
            flash(f"Bienvenido/a (local). {verified_msg}", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            print("Error login local:", e)
            flash("Credenciales incorrectas.", "danger")

    try:
        return render_template("login.html")
    except TemplateNotFound:
        return ("Plantilla login.html no encontrada en: %s" % app.template_folder), 500


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
@load_user_data
def dashboard():
    try:
        return render_template("dashboard.html")
    except TemplateNotFound:
        return ("Plantilla dashboard.html no encontrada en: %s" % app.template_folder), 500


@app.route("/profile")
@login_required
@load_user_data
def profile():
    try:
        return render_template("profile.html")
    except TemplateNotFound:
        return ("Plantilla profile.html no encontrada en: %s" % app.template_folder), 500

# Manejo de errores
@app.errorhandler(404)
def page_not_found(e):
    try:
        return render_template("404.html"), 404
    except TemplateNotFound:
        return ("404 - Página no encontrada"), 404


@app.errorhandler(500)
def server_error(e):
    try:
        # intenta renderizar 500.html si existe
        return render_template("500.html"), 500
    except TemplateNotFound:
        # Información básica para debugging en dev
        return ("500 - Error interno del servidor: %s" % str(e)), 500

# Entry point
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"Iniciando app Flask\nStatic folder: {app.static_folder}\nTemplates folder: {app.template_folder}")
    print(f"AUTH_AVAILABLE: {AUTH_AVAILABLE}\nFIREBASE_ADMIN_AVAILABLE: {FIREBASE_ADMIN_AVAILABLE}")
    # Nota: para que la app sea accesible desde otros dispositivos en la misma red usar host='0.0.0.0'
    app.run(debug=debug_mode, host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
