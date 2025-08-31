# app/main/main_routes.py
"""
Rutas principales y helpers del Blueprint 'main' de PlayTimeUY.

Incluye:
✅ Autenticación Firebase (registro, login, logout)
✅ Protección CSRF y rate limiting
✅ Verificación de edad
✅ Render seguro con fallback amigable
✅ Helpers de sesión y roles
✅ Integración básica de dashboards según rol
✅ Inicialización robusta de Firebase Admin (ruta JSON o variables .env)
"""

from __future__ import annotations

import os
import json
import logging
import secrets
import time
from functools import wraps
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime

import requests
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    make_response,
)
from jinja2 import TemplateNotFound

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth as admin_auth, firestore

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logger = logging.getLogger("PlayTimeUY.main")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

# -------------------------------------------------------------------
# Blueprint
# -------------------------------------------------------------------
main = Blueprint("main", __name__)
# Export con el nombre que espera tu app factory
main_bp = main

# -------------------------------------------------------------------
# Constantes y paths
# -------------------------------------------------------------------
DEFAULT_ROLE = "buyer"
VERIFIED_JSON = os.path.join(
    os.getenv("PLAYTIMEUY_DATA_DIR", os.getcwd()), "verified_users.json"
)

# -------------------------------------------------------------------
# Utilidades de entorno
# -------------------------------------------------------------------
def _env(*keys: str, default: Optional[str] = None) -> Optional[str]:
    """
    Busca la primera variable definida entre las claves provistas.
    """
    for k in keys:
        val = os.getenv(k)
        if val not in (None, ""):
            return val
    return default

def _normalize_private_key(key: str) -> str:
    """
    Normaliza una private key que pudo venir con '\\n' escapados (Windows/.env).
    - Si contiene '\\n' lo convierte a saltos reales.
    - Quita comillas envolventes si existen.
    """
    if not key:
        return key
    key = key.strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1]
    if "\\n" in key and "\n" not in key:
        key = key.replace("\\n", "\n")
    return key

# -------------------------------------------------------------------
# Inicialización robusta de Firebase Admin
#   - Soporta:
#       * FIREBASE_SERVICE_ACCOUNT (ruta al json)
#       * Variables sueltas: FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY
#   - Requiere FIREBASE_DATABASE_URL
#   - API Key web para login por password:
#       * FIREBASE_WEB_API_KEY | FIREBASE_API_KEY | VITE_FIREBASE_API_KEY
# -------------------------------------------------------------------
FIREBASE_DATABASE_URL = _env("FIREBASE_DATABASE_URL")
FIREBASE_WEB_API_KEY = _env("FIREBASE_WEB_API_KEY", "FIREBASE_API_KEY", "VITE_FIREBASE_API_KEY")
SERVICE_ACCOUNT_PATH = _env("FIREBASE_SERVICE_ACCOUNT", "GOOGLE_APPLICATION_CREDENTIALS")

# Construcción/validación de credenciales
firebase_app_name = "playtimeuy"  # nombre estable por si inicias varios contextos

if not FIREBASE_DATABASE_URL:
    logger.error("Falta FIREBASE_DATABASE_URL en el entorno.")
    raise RuntimeError("⚠️ Variables de entorno Firebase no configuradas: falta FIREBASE_DATABASE_URL.")

if not FIREBASE_WEB_API_KEY:
    logger.error("Falta FIREBASE_WEB_API_KEY / FIREBASE_API_KEY / VITE_FIREBASE_API_KEY para el login REST.")
    raise RuntimeError("⚠️ Variables de entorno Firebase no configuradas: falta API key web para login.")

def _build_credentials() -> credentials.Base:
    """
    Crea el objeto credentials.Certificate desde ruta a JSON o variables sueltas.
    """
    # 1) Ruta a service account JSON
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        logger.info("Usando Service Account por ruta: %s", SERVICE_ACCOUNT_PATH)
        return credentials.Certificate(SERVICE_ACCOUNT_PATH)

    # 2) Variables sueltas
    project_id = _env("FIREBASE_PROJECT_ID")
    client_email = _env("FIREBASE_CLIENT_EMAIL")
    private_key = _env("FIREBASE_PRIVATE_KEY")
    if private_key:
        private_key = _normalize_private_key(private_key)

    if not (project_id and client_email and private_key):
        logger.error("Faltan variables para Service Account (PROJECT_ID/CLIENT_EMAIL/PRIVATE_KEY).")
        raise RuntimeError("⚠️ Variables de entorno Firebase no configuradas correctamente.")

    sa_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": _env("FIREBASE_PRIVATE_KEY_ID", "dummy-key-id"),  # opcional
        "private_key": private_key,
        "client_email": client_email,
        "client_id": _env("FIREBASE_CLIENT_ID", "0"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": _env(
            "FIREBASE_CLIENT_CERT_URL",
            f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}"
        ),
    }
    logger.info("Usando Service Account desde variables de entorno (project_id=%s).", project_id)
    return credentials.Certificate(sa_dict)

# Inicializar una sola vez (idempotente)
try:
    if firebase_app_name in firebase_admin._apps:
        _app = firebase_admin.get_app(firebase_app_name)
    elif firebase_admin._apps:
        # Ya hay un app default; reusar
        _app = firebase_admin.get_app()
    else:
        _cred = _build_credentials()
        _app = firebase_admin.initialize_app(_cred, {"databaseURL": FIREBASE_DATABASE_URL}, name=firebase_app_name)
    firestore_db = firestore.client(_app)
    logger.info("✅ Firebase Admin inicializado correctamente (firestore listo).")
except Exception as _exc:
    logger.exception("❌ Error inicializando Firebase Admin: %s", _exc)
    raise

FIREBASE_REST_SIGNIN_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
)

# -------------------------------------------------------------------
# Utils / Edad
# -------------------------------------------------------------------
def get_age(birthdate: datetime) -> int:
    """Calcula edad exacta desde una fecha de nacimiento."""
    today = datetime.now()
    return today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

def _is_minor(birthdate: datetime, min_age: int = 18) -> bool:
    return get_age(birthdate) < min_age

# -------------------------------------------------------------------
# Verified Users JSON (persistencia simple)
# -------------------------------------------------------------------
def load_verified_users() -> List[str]:
    try:
        with open(VERIFIED_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning("No se pudo leer %s (%s). Se continúa con lista vacía.", VERIFIED_JSON, e)
        return []

def save_verified_user(email: str) -> None:
    email = (email or "").strip().lower()
    if not email:
        return
    users = set(load_verified_users())
    if email not in users:
        users.add(email)
        try:
            os.makedirs(os.path.dirname(VERIFIED_JSON), exist_ok=True)
        except Exception:
            pass
        with open(VERIFIED_JSON, "w", encoding="utf-8") as f:
            json.dump(sorted(users), f, indent=2, ensure_ascii=False)

# -------------------------------------------------------------------
# Seguridad: CSRF y Rate Limiting
# -------------------------------------------------------------------
def _get_csrf_token() -> str:
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token

def csrf_protect(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sent = request.headers.get("X-CSRF-Token") or request.form.get("_csrf") or ""
            expected = session.get("_csrf") or ""
            if not sent or not secrets.compare_digest(sent, expected):
                logger.warning("CSRF inválido: %s %s", request.remote_addr, request.path)
                return jsonify({"ok": False, "error": "CSRF inválido"}), 403
        return fn(*args, **kwargs)
    return wrapper

# Un bucket en memoria por IP y endpoint. Suficiente para single-process.
_RATE_BUCKETS: Dict[str, List[float]] = {}
def rate_limit(max_calls: int, per_seconds: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "anon").split(",")[0].strip()
            key = f"{ip}:{fn.__name__}"
            now = time.time()
            bucket = _RATE_BUCKETS.setdefault(key, [])
            # limpiar ventana
            _RATE_BUCKETS[key] = [t for t in bucket if now - t < per_seconds]
            if len(_RATE_BUCKETS[key]) >= max_calls:
                return jsonify({"ok": False, "error": "Demasiadas solicitudes. Intenta más tarde."}), 429
            _RATE_BUCKETS[key].append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# -------------------------------------------------------------------
# Sesión & Auth helpers
# -------------------------------------------------------------------
def get_current_user() -> Optional[Dict[str, Any]]:
    return session.get("user")

def set_current_user(user: Dict[str, Any]) -> None:
    # endurecer un poco la sesión
    session.permanent = True
    session["user"] = {
        "uid": user.get("uid"),
        "email": (user.get("email") or "").lower(),
        "username": user.get("username"),
        "role": user.get("role", DEFAULT_ROLE),
        "is_admin": bool(user.get("is_admin", False)),
    }

def clear_session() -> None:
    session.clear()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            flash("Iniciá sesión para continuar", "warning")
            return redirect(url_for("main.login"))
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or user.get("role") not in roles:
                flash("No tenés permisos para acceder a esta sección", "danger")
                return redirect(url_for("main.dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# -------------------------------------------------------------------
# Render helper con fallback
# -------------------------------------------------------------------
def try_render(template: str, status: int = 200, **ctx):
    ctx.setdefault("csrf_token", _get_csrf_token())
    ctx.setdefault("user", get_current_user())
    try:
        return render_template(template, **ctx), status
    except TemplateNotFound:
        logger.error("Template no encontrado: %s", template)
        # 404 coherente cuando falta template
        return render_template("errors/404.html", missing_template=template), 404
    except Exception as e:
        logger.exception("Error renderizando %s: %s", template, e)
        return render_template("errors/500.html", error=str(e)), 500

# -------------------------------------------------------------------
# Validaciones básicas
# -------------------------------------------------------------------
def _valid_email(email: str) -> bool:
    email = (email or "").strip().lower()
    return bool(email and "@" in email and "." in email.rsplit("@", 1)[-1])

def _valid_password(pw: str) -> bool:
    return bool(pw and len(pw) >= 6)

# -------------------------------------------------------------------
# Firebase helpers (registro/login)
# -------------------------------------------------------------------
def firebase_register(
    email: str,
    password: str,
    username: str,
    role: str = DEFAULT_ROLE
) -> Tuple[Optional[dict], Optional[str]]:
    email = (email or "").lower().strip()
    if not _valid_email(email):
        return None, "Email inválido."
    if not _valid_password(password):
        return None, "La contraseña debe tener al menos 6 caracteres."
    if not (username or "").strip():
        return None, "El nombre de usuario es obligatorio."

    try:
        user_record = admin_auth.create_user(email=email, password=password, display_name=username, app=_app)
        user_data = {
            "uid": user_record.uid,
            "email": email,
            "username": username.strip(),
            "role": role,
            "is_admin": role == "admin",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        firestore_db.collection("users").document(user_record.uid).set(user_data)
        return user_data, None
    except Exception as exc:
        logger.exception("Error creando usuario en Firebase: %s", exc)
        return None, "No se pudo crear el usuario. Revisá el email o intenta más tarde."

def firebase_login_password(email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    email = (email or "").lower().strip()
    if not _valid_email(email) or not password:
        return None, "Email o contraseña inválidos."

    try:
        resp = requests.post(
            FIREBASE_REST_SIGNIN_URL,
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=10,
        )
        data = resp.json()
        if resp.status_code != 200:
            # Mensaje legible
            msg = data.get("error", {}).get("message", "Usuario o contraseña incorrectos.")
            if msg == "INVALID_PASSWORD":
                msg = "Contraseña incorrecta."
            elif msg == "EMAIL_NOT_FOUND":
                msg = "No existe un usuario con ese email."
            return None, msg

        uid = data.get("localId")
        user_ref = firestore_db.collection("users").document(uid)
        snap = user_ref.get()
        if not snap.exists:
            minimal = {
                "uid": uid,
                "email": email,
                "username": data.get("displayName") or email.split("@")[0],
                "role": DEFAULT_ROLE,
                "is_admin": False,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            user_ref.set(minimal)
            return minimal, None

        profile = snap.to_dict() or {}
        # sanea datos mínimos
        profile.setdefault("email", email)
        profile.setdefault("role", DEFAULT_ROLE)
        profile.setdefault("is_admin", False)
        return profile, None

    except Exception as exc:
        logger.exception("Error login Firebase: %s", exc)
        return None, "Error interno autenticando usuario."

# -------------------------------------------------------------------
# Rutas
# -------------------------------------------------------------------
@main.route("/healthz", methods=["GET"])
def healthz():
    try:
        # chequeo simple de firestore
        firestore_db.collection("_healthz").document("ping").set({"ts": datetime.utcnow().isoformat() + "Z"})
        return jsonify({"ok": True, "service": "PlayTimeUY.main", "firebase": "ok"}), 200
    except Exception as e:
        logger.warning("Healthz firestore fallo: %s", e)
        return jsonify({"ok": False, "error": "firebase"}), 500

@main.route("/", methods=["GET"])
def index():
    return try_render("index.html")

@main.route("/verify-age", methods=["GET", "POST"])
def verify_age():
    email = session.get("temp_email")
    if request.method == "POST":
        try:
            day = int(request.form.get("day", "0"))
            month = int(request.form.get("month", "0"))
            year = int(request.form.get("year", "0"))
            birthdate = datetime(year, month, day)
        except Exception:
            flash("Fecha inválida", "danger")
            return try_render("auth/verify_age.html", email=email, status=400)

        if _is_minor(birthdate):
            flash("Debes ser mayor de 18 años para registrarte.", "danger")
            return try_render("auth/verify_age.html", email=email, status=403)

        if email:
            save_verified_user(email)
        flash("Edad verificada con éxito.", "success")
        return redirect(url_for("main.login"))

    return try_render("auth/verify_age.html", email=email)

@main.route("/register", methods=["GET", "POST"])
@csrf_protect
@rate_limit(10, 60)
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()
        username = (request.form.get("username") or "").strip()
        role = (request.form.get("role") or DEFAULT_ROLE).strip()

        user, err = firebase_register(email, password, username, role)
        if user:
            session["temp_email"] = email
            flash("Registro exitoso. Verificá tu edad.", "success")
            return redirect(url_for("main.verify_age"))

        flash(err or "No se pudo crear el usuario", "danger")
        return try_render(
            "auth/register.html",
            status=400,
            form={"email": email, "username": username, "role": role},
        )

    return try_render("auth/register.html")

@main.route("/login", methods=["GET", "POST"])
@csrf_protect
@rate_limit(10, 60)
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()

        user, err = firebase_login_password(email, password)
        if user:
            if email.lower() not in [u.lower() for u in load_verified_users()]:
                session["temp_email"] = email
                flash("Debes verificar tu edad antes de ingresar.", "warning")
                return redirect(url_for("main.verify_age"))

            set_current_user(user)
            flash("Bienvenid@ a PlayTimeUY", "success")
            return redirect(url_for("main.dashboard"))

        flash(err or "Usuario o contraseña incorrectos", "danger")
        return try_render("auth/login.html", status=401, form={"email": email})

    return try_render("auth/login.html")

@main.route("/logout", methods=["POST", "GET"])
@csrf_protect
def logout():
    clear_session()
    flash("Sesión cerrada", "info")
    return redirect(url_for("main.index"))

@main.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    user = get_current_user() or {}
    role = user.get("role", DEFAULT_ROLE)
    tpl_map = {
        "buyer": "home/explorar.html",
        "promoter": "users/promotor.html",
        "creator": "creators/creator_panel.html",
        "admin": "admin/dashboard.html",
    }
    return try_render(tpl_map.get(role, "home/explorar.html"))
