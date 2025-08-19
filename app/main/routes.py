import os
import json
import uuid
import logging
from pathlib import Path
from datetime import timedelta

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────────────────────────────
# Configuración básica
# ────────────────────────────────────────────────────────────────────────
main = Blueprint("main", __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
if not USERS_FILE.exists():
    USERS_FILE.write_text(json.dumps({}, indent=2, ensure_ascii=False))

# ────────────────────────────────────────────────────────────────────────
# Integraciones Firebase
# ────────────────────────────────────────────────────────────────────────
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
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_admin_auth = firebase_admin_auth_module
        FIREBASE_ADMIN_AVAILABLE = True
        USE_FIRESTORE = True
        logger.info("[Firebase Admin] Inicializado correctamente.")
    else:
        logger.warning("[Firebase Admin] Variable GOOGLE_APPLICATION_CREDENTIALS no establecida o archivo inexistente.")
except Exception as e:
    logger.warning("[Firebase Admin] No disponible: %s", e)

# Pyrebase (para email/password y reset password desde servidor si se desea)
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
        logger.info("[Pyrebase] Inicializado correctamente.")
    else:
        logger.warning("[Pyrebase] Falta FIREBASE_API_KEY; Pyrebase deshabilitado.")
except Exception as e:
    logger.warning("[Pyrebase] No disponible: %s", e)

# ────────────────────────────────────────────────────────────────────────
# Helpers de almacenamiento local (fallback)
# ────────────────────────────────────────────────────────────────────────
def load_users():
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")

def create_local_user(email, password, username="", full_name="", role="buyer", extra=None):
    users = load_users()
    if email in users:
        raise ValueError("Email ya registrado.")
    local_id = str(uuid.uuid4())
    users[email] = {
        "localId": local_id,
        "email": email,
        "password_hash": generate_password_hash(password),
        "username": username or email.split("@")[0],
        "full_name": full_name,
        "role": role,
        "emailVerified": True,  # local no tiene verificación real
        "is_admin": False,
        **(extra or {})
    }
    save_users(users)
    return users[email]

def authenticate_local_user(email, password):
    users = load_users()
    user = users.get(email)
    if not user:
        raise ValueError("Usuario no encontrado.")
    if not check_password_hash(user["password_hash"], password):
        raise ValueError("Contraseña incorrecta.")
    return user

# ────────────────────────────────────────────────────────────────────────
# Decoradores y utilidades
# ────────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Inicia sesión primero.", "warning")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return wrapper

def route_for_role(role: str):
    return url_for({
        "buyer": "main.dashboard_buyer",
        "creator": "main.dashboard_creator",
        "promoter": "main.dashboard_promoter"
    }.get(role, "main.dashboard_buyer"))

def get_current_user():
    if "user" not in session:
        return None
    return {
        "uid": session.get("user"),
        "email": session.get("email"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
        "username": session.get("username"),
        "is_admin": session.get("is_admin", False),
    }

@main.app_context_processor
def inject_has_endpoint():
    """Permite usar has_endpoint('blueprint.endpoint') en templates."""
    def has_endpoint(name: str) -> bool:
        try:
            url_for(name)
            return True
        except Exception:
            return False
    return dict(has_endpoint=has_endpoint)

# ────────────────────────────────────────────────────────────────────────
# Rutas principales
# ────────────────────────────────────────────────────────────────────────
@main.route("/")
def index():
    return render_template("home/index.html", user=get_current_user())

# Registro (email/password)
@main.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(route_for_role(session.get("role", "buyer")))

    if request.method == "POST":
        # Honeypot anti-bot
        if request.form.get("website"):
            flash("Error en formulario.", "danger")
            return redirect(url_for("main.register"))

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        username = (request.form.get("username") or "").strip() or email.split("@")[0]
        role = (request.form.get("role") or "buyer").strip()

        if password != confirm:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("main.register"))
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for("main.register"))

        # Intento con Firebase (si está disponible)
        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.create_user_with_email_and_password(email, password)
                login_user = firebase_auth.sign_in_with_email_and_password(email, password)
                # Enviar verificación de correo
                firebase_auth.send_email_verification(login_user["idToken"])
                local_id = user.get("localId", str(uuid.uuid4()))
                if USE_FIRESTORE and db:
                    db.collection("usuarios").document(local_id).set({
                        "full_name": full_name,
                        "username": username,
                        "email": email,
                        "role": role,
                        "is_admin": False,
                        "verified": False,
                    })
                flash("✅ Revisa tu correo y verifica tu cuenta para continuar.", "success")
                return redirect(url_for("main.login"))
            except Exception as e:
                logger.warning("Firebase register error: %s", e)
                # Continúa a fallback local sin mensajes crudos
                flash("No se pudo registrar con el servicio remoto. Se utilizará el registro local.", "warning")

        # Fallback local
        try:
            create_local_user(email, password, username, full_name, role)
            flash("Registro local exitoso. Ahora podés iniciar sesión.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("auth/register.html")

# Login (email/password)
@main.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(route_for_role(session.get("role", "buyer")))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        # Firebase
        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.sign_in_with_email_and_password(email, password)
                info = firebase_auth.get_account_info(user["idToken"])
                firebase_user = info["users"][0]
                if not firebase_user.get("emailVerified", False):
                    flash("Debes verificar tu correo antes de ingresar.", "warning")
                    return redirect(url_for("main.login"))

                session["user"] = firebase_user.get("localId") or firebase_user.get("uid") or str(uuid.uuid4())
                session["email"] = email
                session["role"] = "buyer"

                if USE_FIRESTORE and db:
                    doc = db.collection("usuarios").document(session["user"]).get()
                    if doc.exists:
                        session["role"] = doc.to_dict().get("role", "buyer")

                # Recordarme
                session.permanent = remember
                if remember:
                    current_app.permanent_session_lifetime = timedelta(days=30)

                flash("Bienvenido.", "success")
                return redirect(route_for_role(session["role"]))
            except Exception as e:
                logger.warning("Firebase login error: %s", e)
                flash("No se pudo autenticar con el servicio remoto. Probá de nuevo o usa el acceso local.", "warning")

        # Fallback local
        try:
            user = authenticate_local_user(email, password)
            session["user"] = user["localId"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            session.permanent = remember
            if remember:
                current_app.permanent_session_lifetime = timedelta(days=30)

            flash("Bienvenido.", "success")
            return redirect(route_for_role(session["role"]))
        except Exception as e:
            logger.info("Local login error: %s", e)
            flash("Credenciales incorrectas.", "danger")

    return render_template("auth/login.html")

# Logout
@main.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("main.login"))

# ────────────────────────────────────────────────────────────────────────
# Recuperación de contraseña
# ────────────────────────────────────────────────────────────────────────
@main.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Ingresá un correo válido.", "danger")
            return redirect(url_for("main.forgot_password"))

        # Enviar email de reset con Firebase si está disponible
        if AUTH_AVAILABLE and firebase_auth:
            try:
                firebase_auth.send_password_reset_email(email)
                flash("📩 Te enviamos un enlace para restablecer tu contraseña.", "success")
                return redirect(url_for("main.login"))
            except Exception as e:
                logger.warning("Error enviando reset password con Firebase: %s", e)
                flash("No se pudo enviar el correo de recuperación. Intenta nuevamente.", "danger")
                return redirect(url_for("main.forgot_password"))

        # Si no hay Firebase, mensaje informativo
        flash("La recuperación de contraseña requiere el servicio remoto habilitado.", "warning")
        return redirect(url_for("main.forgot_password"))

    return render_template("auth/forgot_password.html")

# ────────────────────────────────────────────────────────────────────────
# Login con Google (desde frontend: /login/google con idToken)
# ────────────────────────────────────────────────────────────────────────
@main.route("/login/google", methods=["POST"])
def login_google():
    """
    Endpoint para el auth.js del frontend:
      - Recibe { "idToken": "<token_de_firebase>" }
      - Verifica el token con Firebase Admin
      - Inicia sesión de servidor y redirige al dashboard según rol
    """
    data = request.get_json(silent=True) or {}
    id_token = data.get("idToken")

    if not id_token:
        return jsonify({"ok": False, "error": "Falta idToken"}), 400

    if not FIREBASE_ADMIN_AVAILABLE or not firebase_admin_auth:
        # No podemos verificar el token sin Firebase Admin
        return jsonify({"ok": False, "error": "Verificación de token no disponible en el servidor."}), 503

    try:
        decoded = firebase_admin_auth.verify_id_token(id_token)
        uid = decoded.get("uid")
        email = (decoded.get("email") or "").lower()
        email_verified = decoded.get("email_verified", False)
        name = decoded.get("name", "")
        username = email.split("@")[0] if email else f"user-{uid[:6]}"

        if not email_verified:
            return jsonify({"ok": False, "error": "Correo no verificado"}), 401

        # Determinar rol desde Firestore si existe, sino buyer
        role = "buyer"
        if USE_FIRESTORE and db and uid:
            doc = db.collection("usuarios").document(uid).get()
            if doc.exists:
                role = doc.to_dict().get("role", "buyer")
            else:
                # Crear documento mínimo si no existe
                db.collection("usuarios").document(uid).set({
                    "email": email,
                    "full_name": name,
                    "username": username,
                    "role": role,
                    "is_admin": False,
                    "verified": True,
                    "provider": "google"
                })

        # Sesión
        session["user"] = uid
        session["email"] = email
        session["full_name"] = name
        session["username"] = username
        session["role"] = role
        session["is_admin"] = False

        # Redirección final (el frontend detecta .redirected)
        return redirect(route_for_role(role))
    except Exception as e:
        logger.warning("Google login token verify error: %s", e)
        return jsonify({"ok": False, "error": "Token inválido o expirado."}), 401

# ────────────────────────────────────────────────────────────────────────
# Dashboards
# ────────────────────────────────────────────────────────────────────────
@main.route("/dashboard")
@login_required
def dashboard():
    return redirect(route_for_role(session.get("role", "buyer")))

@main.route("/dashboard/buyer")
@login_required
def dashboard_buyer():
    return render_template("users/user_panel.html", user=get_current_user())

@main.route("/dashboard/creator")
@login_required
def dashboard_creator():
    return render_template("creators/creator_panel.html", user=get_current_user())

@main.route("/dashboard/promoter")
@login_required
def dashboard_promoter():
    return render_template("users/promotor.html", user=get_current_user())
