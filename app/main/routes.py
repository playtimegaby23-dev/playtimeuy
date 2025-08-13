import os
import json
import uuid
from pathlib import Path
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

main = Blueprint("main", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Firebase Admin y Firestore ---
FIREBASE_ADMIN_AVAILABLE = False
USE_FIRESTORE = False
db = None
firebase_admin_auth = None

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_admin_auth_module, firestore
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_admin_auth = firebase_admin_auth_module
        FIREBASE_ADMIN_AVAILABLE = True
        USE_FIRESTORE = True
    else:
        print("[Firebase Admin] GOOGLE_APPLICATION_CREDENTIALS no configurado o no existe.")
except Exception as e:
    print("[Firebase Admin] No disponible o error en inicialización:", e)

# --- Pyrebase para autenticación ---
AUTH_AVAILABLE = False
firebase_auth = None

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
        firebase_auth = firebase.auth()
        AUTH_AVAILABLE = True
    else:
        print("[Pyrebase] Configuración incompleta, auth no disponible.")
except Exception as e:
    print("[Pyrebase] No disponible:", e)

# --- Manejo local de usuarios (fallback) ---
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

# --- Decoradores ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

def load_user_data(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' in session:
            uid = session['user']
            if USE_FIRESTORE and db:
                try:
                    doc = db.collection("usuarios").document(uid).get()
                    if doc.exists:
                        d = doc.to_dict()
                        session['role'] = d.get('role', 'buyer')
                        session['is_admin'] = d.get('is_admin', False)
                    else:
                        session.clear()
                        flash("Usuario no encontrado. Inicia sesión nuevamente.", "danger")
                        return redirect(url_for('main.login'))
                except Exception as e:
                    print("[Firestore] Error cargando datos de usuario:", e)
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
                    return redirect(url_for('main.login'))
                session['role'] = found.get('role', 'buyer')
                session['is_admin'] = found.get('is_admin', False)
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user' not in session:
        return None
    return {
        "uid": session['user'],
        "email": session.get('email'),
        "role": session.get('role', 'buyer'),
        "is_admin": session.get('is_admin', False)
    }

# --- Rutas ---
@main.route("/")
def index():
    return render_template("index.html", user=get_current_user())

@main.route("/register", methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        username = request.form.get("username") or (email.split("@")[0] if email else "")
        full_name = request.form.get("full_name", "").strip()

        if not email or not password:
            flash("Email y contraseña son requeridos.", "danger")
            return redirect(url_for("main.register"))
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("main.register"))
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for("main.register"))

        # Intentar registrar en Firebase remoto
        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.create_user_with_email_and_password(email, password)
                local_id = user.get('localId')
                if not local_id:
                    # Intentar obtener UID de user['localId'] o fallback
                    local_id = user.get('localId', str(uuid.uuid4()))
                if USE_FIRESTORE and db:
                    db.collection("usuarios").document(local_id).set({
                        "full_name": full_name,
                        "username": username,
                        "email": email,
                        "role": "buyer",
                        "is_admin": False
                    })
                flash("Registro exitoso. Verifica tu correo si es necesario.", "success")
                return redirect(url_for("main.login"))
            except Exception as e:
                print("[Firebase Register] Error:", e)
                flash(f"No se pudo registrar en remoto: {e}", "warning")

        # Registro local fallback
        try:
            create_local_user(email, password, username, full_name)
            flash("Registro local exitoso.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email y contraseña son requeridos.", "danger")
            return redirect(url_for("main.login"))

        # Intentar login remoto con Pyrebase
        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.sign_in_with_email_and_password(email, password)
                session['user'] = user.get('localId')
                session['email'] = email
                flash("Bienvenido/a (remoto).", "success")
                return redirect(url_for("main.dashboard"))
            except Exception as e:
                print("[Firebase Login] Error:", e)
                flash("Fallo remoto, intentando local.", "warning")

        # Login local fallback
        try:
            user = authenticate_local_user(email, password)
            session['user'] = user["localId"]
            session['email'] = user["email"]
            flash("Bienvenido/a (local).", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            print("[Local Login] Error:", e)
            flash("Credenciales incorrectas.", "danger")

    return render_template("login.html")

@main.route("/login/google", methods=["POST"])
def login_google():
    from flask import request
    id_token = request.json.get("idToken")
    if not id_token:
        return {"error": "No token provided"}, 400
    if not FIREBASE_ADMIN_AVAILABLE or not firebase_admin_auth:
        flash("Servicio Google login no disponible.", "danger")
        return redirect(url_for("main.login"))

    try:
        decoded_token = firebase_admin_auth.verify_id_token(id_token)
        session["user"] = decoded_token["uid"]
        session["email"] = decoded_token.get("email")
        flash("Inicio de sesión con Google exitoso.", "success")
        return redirect(url_for("main.dashboard"))
    except Exception as e:
        print("Error verificando token Firebase:", e)
        flash("Error autenticando con Google.", "danger")
        return redirect(url_for("main.login"))

@main.route("/dashboard")
@login_required
@load_user_data
def dashboard():
    return render_template("dashboard.html", user=get_current_user())

@main.route("/profile")
@login_required
@load_user_data
def profile():
    return render_template("profile.html", user=get_current_user())

@main.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("main.login"))

@main.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@main.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500
