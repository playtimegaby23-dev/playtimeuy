"""
Rutas principales de la aplicación con autenticación y nueva estructura de templates
"""

import os
import json
import uuid
from pathlib import Path
from functools import wraps
from datetime import timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

main = Blueprint("main", __name__)

# ------------------- DIRECTORIOS -------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ------------------- FIREBASE ADMIN & FIRESTORE -------------------
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
    else:
        print("[Firebase Admin] GOOGLE_APPLICATION_CREDENTIALS no configurado o no existe.")
except Exception as e:
    print("[Firebase Admin] No disponible o error en inicialización:", e)

# ------------------- PYREBASE (Autenticación) -------------------
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

# ------------------- FALLBACK LOCAL -------------------
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


def create_local_user(email, password, username="", full_name="", role="buyer", extra=None):
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
        "emailVerified": True,
        "role": role if role in {"buyer", "creator", "promoter"} else "buyer",
        "is_admin": False,
        **(extra or {})
    }
    save_users(users)
    return users[email]


def update_local_user(email, fields: dict):
    users = load_users()
    if email not in users:
        return
    users[email].update(fields)
    save_users(users)


def get_local_user_by_uid(uid):
    users = load_users()
    for _, u in users.items():
        if u.get("localId") == uid:
            return u
    return None


def authenticate_local_user(email, password):
    users = load_users()
    user = users.get(email)
    if not user:
        raise ValueError("Usuario no encontrado (local).")
    if not check_password_hash(user["password_hash"], password):
        raise ValueError("Contraseña incorrecta (local).")
    return user


# ------------------- HELPERS / DECORADORES -------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                flash("Por favor, inicia sesión para acceder a esta página.", "warning")
                return redirect(url_for('main.login'))
            user_role = session.get('role', 'buyer')
            if roles and user_role not in roles:
                flash("No tenés permiso para acceder a esta sección.", "danger")
                return redirect(route_for_role(user_role))
            return f(*args, **kwargs)
        return decorated
    return wrapper


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
                        session['full_name'] = d.get('full_name')
                        session['username'] = d.get('username')
                    else:
                        session.clear()
                        flash("Usuario no encontrado. Iniciá sesión nuevamente.", "danger")
                        return redirect(url_for('main.login'))
                except Exception as e:
                    print("[Firestore] Error cargando datos de usuario:", e)
                    session.setdefault('role', 'buyer')
                    session.setdefault('is_admin', False)
            else:
                found = get_local_user_by_uid(uid)
                if not found:
                    session.clear()
                    flash("Usuario no encontrado (local). Iniciá sesión nuevamente.", "danger")
                    return redirect(url_for('main.login'))
                session['role'] = found.get('role', 'buyer')
                session['is_admin'] = found.get('is_admin', False)
                session['full_name'] = found.get('full_name')
                session['username'] = found.get('username')
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if 'user' not in session:
        return None
    return {
        "uid": session['user'],
        "email": session.get('email'),
        "role": session.get('role', 'buyer'),
        "is_admin": session.get('is_admin', False),
        "full_name": session.get('full_name'),
        "username": session.get('username')
    }


def route_for_role(role: str):
    mapping = {
        "buyer": "main.dashboard_buyer",
        "creator": "main.dashboard_creator",
        "promoter": "main.dashboard_promoter",
    }
    endpoint = mapping.get(role, "main.dashboard_buyer")
    return url_for(endpoint)


def basic_field(value: str) -> str:
    return (value or "").strip()


def validate_register_form(form):
    email = basic_field(form.get("email"))
    password = form.get("password") or ""
    confirm_password = form.get("confirm_password") or ""
    username = basic_field(form.get("username")) or (email.split("@")[0] if email else "")
    full_name = basic_field(form.get("full_name"))
    role = (form.get("role") or "buyer").strip()
    dob = basic_field(form.get("dob"))
    country = basic_field(form.get("country"))
    twitter = basic_field(form.get("twitter"))
    instagram = basic_field(form.get("instagram"))

    if not email or not password:
        return None, "Email y contraseña son requeridos."

    if password != confirm_password:
        return None, "Las contraseñas no coinciden."

    if len(password) < 6:
        return None, "La contraseña debe tener al menos 6 caracteres."

    if role not in {"buyer", "creator", "promoter"}:
        return None, "Rol inválido."

    payload = {
        "email": email,
        "password": password,
        "username": username,
        "full_name": full_name,
        "role": role,
        "dob": dob,
        "country": country,
        "twitter": twitter,
        "instagram": instagram,
    }
    return payload, None


# ------------------- RUTAS -------------------
@main.route("/")
def index():
    return render_template("home/index.html", user=get_current_user())


# ---------- Registro ----------
@main.route("/register", methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect(route_for_role(session.get("role", "buyer")))

    if request.method == "POST":
        if basic_field(request.form.get("website")):
            flash("Error en el formulario.", "danger")
            return redirect(url_for("main.register"))

        data, err = validate_register_form(request.form)
        if err:
            flash(err, "danger")
            return redirect(url_for("main.register"))

        email = data["email"]
        password = data["password"]
        username = data["username"]
        full_name = data["full_name"]
        role = data["role"]

        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.create_user_with_email_and_password(email, password)
                login_user = firebase_auth.sign_in_with_email_and_password(email, password)
                firebase_auth.send_email_verification(login_user['idToken'])

                local_id = user.get('localId', str(uuid.uuid4()))
                if USE_FIRESTORE and db:
                    db.collection("usuarios").document(local_id).set({
                        "full_name": full_name,
                        "username": username,
                        "email": email,
                        "role": role,
                        "is_admin": False,
                        "verified": False,
                        "dob": data["dob"],
                        "country": data["country"],
                        "twitter": data["twitter"],
                        "instagram": data["instagram"],
                    })

                flash("Registro exitoso. Revisá tu correo y verificá tu cuenta antes de iniciar sesión.", "success")
                return redirect(url_for("main.login"))
            except Exception as e:
                print("[Firebase Register] Error:", e)
                flash("No se pudo registrar en remoto, probamos modo local.", "warning")

        try:
            extra = {
                "dob": data["dob"],
                "country": data["country"],
                "twitter": data["twitter"],
                "instagram": data["instagram"],
            }
            create_local_user(email, password, username, full_name, role, extra=extra)
            flash("Registro local exitoso. Ya podés iniciar sesión.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("auth/register.html")


# ---------- Login ----------
@main.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(route_for_role(session.get("role", "buyer")))

    if request.method == "POST":
        email = basic_field(request.form.get("email"))
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Email y contraseña son requeridos.", "danger")
            return redirect(url_for("main.login"))

        if AUTH_AVAILABLE and firebase_auth:
            try:
                user = firebase_auth.sign_in_with_email_and_password(email, password)
                info = firebase_auth.get_account_info(user["idToken"])
                email_verified = info["users"][0].get("emailVerified", False)

                if not email_verified:
                    flash("Debés verificar tu correo antes de acceder.", "warning")
                    return redirect(url_for("main.login"))

                session['user'] = user.get('localId')
                session['email'] = email

                session.permanent = remember
                if remember:
                    current_app.permanent_session_lifetime = timedelta(days=30)

                role = "buyer"
                if USE_FIRESTORE and db:
                    try:
                        doc = db.collection("usuarios").document(session['user']).get()
                        if doc.exists:
                            role = doc.to_dict().get("role", "buyer")
                    except Exception as e:
                        print("[Firestore] Error obteniendo rol:", e)

                session['role'] = role
                flash("Bienvenido/a.", "success")
                return redirect(route_for_role(role))
            except Exception as e:
                print("[Firebase Login] Error:", e)
                flash("Fallo remoto, intentamos modo local.", "warning")

        try:
            user = authenticate_local_user(email, password)
            if not user.get("emailVerified", False):
                flash("Debés verificar tu correo antes de acceder. (local)", "warning")
                return redirect(url_for("main.login"))
            session['user'] = user["localId"]
            session['email'] = user["email"]
            session['role'] = user.get("role", "buyer")

            session.permanent = remember
            if remember:
                current_app.permanent_session_lifetime = timedelta(days=30)

            flash("Bienvenido/a.", "success")
            return redirect(route_for_role(session['role']))
        except Exception as e:
            print("[Local Login] Error:", e)
            flash("Credenciales incorrectas.", "danger")

    return render_template("auth/login.html")


# ---------- Google Login ----------
@main.route("/login/google", methods=["POST"])
def login_google():
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
        role = "buyer"
        if USE_FIRESTORE and db:
            try:
                doc = db.collection("usuarios").document(session["user"]).get()
                if doc.exists:
                    role = doc.to_dict().get("role", "buyer")
            except Exception as e:
                print("[Firestore] Error rol Google:", e)
        session["role"] = role
        flash("Inicio de sesión con Google exitoso.", "success")
        return redirect(route_for_role(role))
    except Exception as e:
        print("Error verificando token Firebase:", e)
        flash("Error autenticando con Google.", "danger")
        return redirect(url_for("main.login"))


# ---------- Dashboards ----------
@main.route("/dashboard")
@login_required
@load_user_data
def dashboard():
    role = session.get("role", "buyer")
    return redirect(route_for_role(role))


@main.route("/dashboard/buyer")
@login_required
@load_user_data
@role_required("buyer")
def dashboard_buyer():
    return render_template("users/user_panel.html", user=get_current_user())


@main.route("/dashboard/creator")
@login_required
@load_user_data
@role_required("creator")
def dashboard_creator():
    return render_template("creators/creator_panel.html", user=get_current_user())


@main.route("/dashboard/promoter")
@login_required
@load_user_data
@role_required("promoter")
def dashboard_promoter():
    return render_template("users/promotor.html", user=get_current_user())


@main.route("/dashboard/admin")
@login_required
@load_user_data
@role_required("admin")
def dashboard_admin():
    return render_template("admin/admindashboard.html", user=get_current_user())


# ---------- Perfil ----------
@main.route("/profile")
@login_required
@load_user_data
def profile():
    return render_template("users/profile.html", user=get_current_user())


# ---------- Logout ----------
@main.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("main.login"))


# ------------------- ERRORES -------------------
@main.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@main.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500
