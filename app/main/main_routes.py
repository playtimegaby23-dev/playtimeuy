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
✅ Inicialización robusta de Firebase Admin
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
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from jinja2 import TemplateNotFound
import firebase_admin
from firebase_admin import credentials, auth as admin_auth, firestore

# ---------------- Logging ----------------
logger = logging.getLogger("PlayTimeUY.main")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------- Blueprint ----------------
main_bp = Blueprint("main", __name__, template_folder="../../templates")

# ---------------- Constantes ----------------
DEFAULT_ROLE = "buyer"
ALLOWED_ROLES = {"buyer", "promoter", "creator", "admin"}
VERIFIED_JSON = os.path.join(os.getenv("PLAYTIMEUY_DATA_DIR", os.getcwd()), "verified_users.json")

# ---------------- Entorno ----------------
def _env(*keys: str, default: Optional[str] = None) -> Optional[str]:
    for k in keys:
        val = os.getenv(k)
        if val:
            return val
    return default

def _normalize_private_key(key: str) -> str:
    if not key:
        return key
    key = key.strip()
    if key.startswith(("'", '"')) and key.endswith(("'", '"')):
        key = key[1:-1]
    return key.replace("\\n", "\n")

# ---------------- Firebase Admin ----------------
FIREBASE_DATABASE_URL = _env("FIREBASE_DATABASE_URL")
FIREBASE_WEB_API_KEY = _env("FIREBASE_WEB_API_KEY", "FIREBASE_API_KEY", "VITE_FIREBASE_API_KEY")
SERVICE_ACCOUNT_PATH = _env("FIREBASE_SERVICE_ACCOUNT", "GOOGLE_APPLICATION_CREDENTIALS")

if not FIREBASE_DATABASE_URL or not FIREBASE_WEB_API_KEY:
    raise RuntimeError("⚠️ Falta configuración de Firebase en el entorno.")

def _build_credentials() -> credentials.Base:
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        logger.info("🔑 Usando Service Account por ruta: %s", SERVICE_ACCOUNT_PATH)
        return credentials.Certificate(SERVICE_ACCOUNT_PATH)

    project_id = _env("FIREBASE_PROJECT_ID")
    client_email = _env("FIREBASE_CLIENT_EMAIL")
    private_key = _normalize_private_key(_env("FIREBASE_PRIVATE_KEY", ""))

    if not (project_id and client_email and private_key):
        raise RuntimeError("⚠️ Faltan variables de entorno para Service Account.")

    sa_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": _env("FIREBASE_PRIVATE_KEY_ID", "dummy"),
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
    logger.info("🔑 Usando Service Account desde variables de entorno (project_id=%s)", project_id)
    return credentials.Certificate(sa_dict)

# Inicialización robusta
firebase_app_name = "playtimeuy"
try:
    if firebase_app_name in firebase_admin._apps:
        _app = firebase_admin.get_app(firebase_app_name)
    elif firebase_admin._apps:
        _app = firebase_admin.get_app()
    else:
        _cred = _build_credentials()
        _app = firebase_admin.initialize_app(_cred, {"databaseURL": FIREBASE_DATABASE_URL}, name=firebase_app_name)
    firestore_db = firestore.client(_app)
    logger.info("✅ Firebase Admin inicializado correctamente.")
except Exception as exc:
    logger.exception("❌ Error inicializando Firebase Admin: %s", exc)
    raise

FIREBASE_REST_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# ---------------- Helpers de sesión ----------------
def get_current_user() -> Optional[Dict[str, Any]]:
    return session.get("user")

def set_current_user(user: Dict[str, Any]) -> None:
    session.permanent = True
    session["user"] = {
        "uid": user.get("uid"),
        "email": (user.get("email") or "").lower(),
        "username": user.get("username"),
        "role": user.get("role", DEFAULT_ROLE),
        "is_admin": bool(user.get("is_admin")),
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

# ---------------- CSRF y Rate Limiting ----------------
def _get_csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]

def csrf_protect(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sent = (
                request.headers.get("X-CSRF-Token")
                or request.form.get("_csrf")
                or (request.headers.get("Authorization", "").removeprefix("Bearer ").strip())
            )
            if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
                logger.warning("❌ CSRF inválido: %s %s", request.remote_addr, request.path)
                return jsonify({"ok": False, "error": "CSRF inválido"}), 403
        return fn(*args, **kwargs)
    return wrapper

_RATE_BUCKETS: Dict[str, List[float]] = {}
def rate_limit(max_calls: int, per_seconds: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "anon").split(",")[0]
            key = f"{user.get('uid') if user else ip}:{fn.__name__}"
            now = time.time()
            _RATE_BUCKETS[key] = [t for t in _RATE_BUCKETS.get(key, []) if now - t < per_seconds]
            if len(_RATE_BUCKETS[key]) >= max_calls:
                return jsonify({"ok": False, "error": "Demasiadas solicitudes"}), 429
            _RATE_BUCKETS[key].append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ---------------- Validaciones ----------------
def _valid_email(email: str) -> bool:
    return bool(email and "@" in email)

def _valid_password(pw: str) -> bool:
    return bool(pw and len(pw) >= 6)

# ---------------- Edad ----------------
def get_age(birthdate: datetime) -> int:
    today = datetime.now()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def _is_minor(birthdate: datetime, min_age: int = 18) -> bool:
    return get_age(birthdate) < min_age

# ---------------- Persistencia simple ----------------
def load_verified_users() -> List[str]:
    try:
        with open(VERIFIED_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_verified_user(email: str) -> None:
    email = (email or "").strip().lower()
    if not email:
        return
    users = set(load_verified_users())
    if email not in users:
        users.add(email)
        os.makedirs(os.path.dirname(VERIFIED_JSON), exist_ok=True)
        with open(VERIFIED_JSON, "w", encoding="utf-8") as f:
            json.dump(sorted(users), f, indent=2, ensure_ascii=False)

# ---------------- Render helper ----------------
def try_render(template: str, status: int = 200, **ctx):
    ctx.setdefault("csrf_token", _get_csrf_token())
    ctx.setdefault("user", get_current_user())
    try:
        return render_template(template, **ctx), status
    except TemplateNotFound:
        logger.error("❌ Template no encontrado: %s", template)
        return render_template("errors/404.html", missing_template=template), 404
    except Exception as e:
        logger.exception("❌ Error renderizando %s: %s", template, e)
        return render_template("errors/500.html", error=str(e)), 500
