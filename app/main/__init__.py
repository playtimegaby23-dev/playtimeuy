# app/main/__init__.py
"""
Blueprint 'main' de PlayTimeUY: rutas y helpers principales.

Incluye:
✅ Autenticación Firebase (registro, login, logout)
✅ Protección CSRF y rate limiting
✅ Verificación de edad
✅ Render seguro con fallback amigable
✅ Helpers de sesión y roles
✅ Integración básica de dashboards según rol
"""

import os
import json
import logging
import secrets
import time
from functools import wraps
from typing import List
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

# ---------------- Logging ----------------
logger = logging.getLogger("PlayTimeUY.main")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------- Blueprint ----------------
main_bp = Blueprint("main", __name__)

# ---------------- Constantes ----------------
DEFAULT_ROLE = "buyer"
VERIFIED_JSON = "verified_users.json"

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_API_KEY")

if not (SERVICE_ACCOUNT_PATH and FIREBASE_DATABASE_URL and FIREBASE_WEB_API_KEY):
    raise RuntimeError("⚠️ Variables de entorno Firebase no configuradas correctamente.")

# ---------------- Inicialización Firebase ----------------
try:
    import firebase_admin
    from firebase_admin import credentials, auth as admin_auth, firestore

    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
    firestore_db = firestore.client()
    logger.info("✅ Firebase Admin inicializado en main")
except Exception as e:
    raise RuntimeError(f"❌ No se pudo inicializar Firebase Admin SDK: {e}")

FIREBASE_REST_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# ---------------- Utils ----------------
def get_age(birthdate: datetime) -> int:
    today = datetime.now()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def _is_minor(birthdate: datetime, min_age: int = 18) -> bool:
    return get_age(birthdate) < min_age

# ---------------- Verified Users ----------------
def load_verified_users() -> List[str]:
    try:
        if not os.path.exists(VERIFIED_JSON):
            return []
        with open(VERIFIED_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error cargando verified_users.json: {e}")
        return []

def save_verified_user(email: str) -> None:
    try:
        users = load_verified_users()
        if email not in users:
            users.append(email)
            with open(VERIFIED_JSON, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)
    except Exception as e:
        logger.error("Error guardando usuario verificado: %s", e)

# ---------------- Decorators y helpers ----------------
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

def rate_limit(max_calls: int, per_seconds: int):
    _RATE_BUCKETS: dict[str, list[float]] = {}
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "anon"
            key = f"{ip}:{fn.__name__}"
            now = time.time()
            bucket = _RATE_BUCKETS.setdefault(key, [])
            _RATE_BUCKETS[key] = [t for t in bucket if now - t < per_seconds]
            if len(_RATE_BUCKETS[key]) >= max_calls:
                return jsonify({"ok": False, "error": "Demasiadas solicitudes. Intenta más tarde."}), 429
            _RATE_BUCKETS[key].append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
