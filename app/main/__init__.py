# app/main/__init__.py
"""
Blueprint 'main' de PlayTimeUY: rutas y helpers principales.

Incluye:
✅ Inicialización robusta de Firebase Admin (ruta JSON / JSON embebido / vars sueltas)
✅ Autenticación Firebase (Admin SDK + REST URL disponible)
✅ Protección CSRF y rate limiting
✅ Verificación de edad
✅ Persistencia simple de usuarios verificados
✅ Helpers utilitarios y logging profesional
✅ Health check
"""

from __future__ import annotations

import os
import json
import logging
import secrets
import time
from pathlib import Path
from functools import wraps
from typing import List, Optional, Dict, Any
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    jsonify,
)
from jinja2 import TemplateNotFound

# =========================================================
# Logging
# =========================================================
logger = logging.getLogger("PlayTimeUY.main")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)

logger.setLevel(
    logging.DEBUG
    if str(os.getenv("FLASK_DEBUG", "0")).lower() in ("1", "true")
    else logging.INFO
)

# =========================================================
# Blueprint
# =========================================================
main_bp = Blueprint("main", __name__)

# =========================================================
# Utilidades de entorno
# =========================================================
def _env(*keys: str, default: Optional[str] = None) -> Optional[str]:
    """Devuelve la primera variable de entorno definida entre las claves."""
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default


def _normalize_private_key(key: str) -> str:
    """Normaliza private_key que puede venir con `\\n` escapados en .env (Windows)."""
    if not key:
        return key
    key = key.strip()
    if key.startswith(("'", '"')) and key.endswith(("'", '"')):
        key = key[1:-1]
    return key.replace("\\n", "\n")

# =========================================================
# Constantes / Paths
# =========================================================
DEFAULT_ROLE = "buyer"

DATA_DIR = Path(_env("PLAYTIMEUY_DATA_DIR", default=str(Path.cwd() / "data"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
VERIFIED_JSON_PATH = DATA_DIR / "verified_users.json"

# =========================================================
# Firebase Admin SDK
# =========================================================
FIREBASE_DATABASE_URL = _env("FIREBASE_DATABASE_URL")
FIREBASE_WEB_API_KEY = _env("FIREBASE_WEB_API_KEY", "FIREBASE_API_KEY", "VITE_FIREBASE_API_KEY")

if not FIREBASE_DATABASE_URL:
    raise RuntimeError("⚠️ Falta FIREBASE_DATABASE_URL en el entorno.")
if not FIREBASE_WEB_API_KEY:
    raise RuntimeError("⚠️ Falta la Web API Key de Firebase.")

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_obj = None

    # 1) JSON completo embebido en env
    json_env = _env("FIREBASE_CREDENTIALS_JSON")
    if json_env:
        try:
            cred_obj = credentials.Certificate(json.loads(json_env))
            logger.info("🔹 Credenciales Firebase cargadas desde FIREBASE_CREDENTIALS_JSON")
        except Exception as exc:
            logger.exception("Credenciales JSON inválidas en FIREBASE_CREDENTIALS_JSON: %s", exc)
            raise

    # 2) Ruta a JSON
    if cred_obj is None:
        service_account_path = _env("FIREBASE_SERVICE_ACCOUNT", "GOOGLE_APPLICATION_CREDENTIALS")
        if service_account_path and Path(service_account_path).exists():
            cred_obj = credentials.Certificate(service_account_path)
            logger.info("🔹 Service Account cargado desde ruta: %s", service_account_path)

    # 3) Vars sueltas
    if cred_obj is None:
        project_id = _env("FIREBASE_PROJECT_ID")
        client_email = _env("FIREBASE_CLIENT_EMAIL")
        private_key = _normalize_private_key(_env("FIREBASE_PRIVATE_KEY", ""))

        if not (project_id and client_email and private_key):
            raise RuntimeError(
                "⚠️ No se encontraron credenciales válidas. "
                "Configura FIREBASE_CREDENTIALS_JSON, FIREBASE_SERVICE_ACCOUNT o "
                "FIREBASE_PROJECT_ID + FIREBASE_CLIENT_EMAIL + FIREBASE_PRIVATE_KEY."
            )

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
        cred_obj = credentials.Certificate(sa_dict)
        logger.info("🔹 Service Account construido desde variables de entorno (project_id=%s)", project_id)

    # Inicializar Firebase Admin
    if firebase_admin._apps:
        _app = firebase_admin.get_app()
        logger.info("♻️ Firebase Admin ya estaba inicializado, reusando app.")
    else:
        _app = firebase_admin.initialize_app(cred_obj, {"databaseURL": FIREBASE_DATABASE_URL})
        logger.info("✅ Firebase Admin inicializado (databaseURL=%s)", FIREBASE_DATABASE_URL)

    firestore_db = firestore.client(_app)

except Exception as e:
    logger.exception("❌ No se pudo inicializar Firebase Admin")
    raise RuntimeError(f"No se pudo inicializar Firebase Admin SDK: {e}") from e

FIREBASE_REST_SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# =========================================================
# Helpers de edad
# =========================================================
def get_age(birthdate: datetime) -> int:
    today = datetime.now()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


def is_minor(birthdate: datetime, min_age: int = 18) -> bool:
    return get_age(birthdate) < min_age

# =========================================================
# Verified Users
# =========================================================
def load_verified_users() -> List[str]:
    try:
        if not VERIFIED_JSON_PATH.exists():
            return []
        with open(VERIFIED_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("No se pudo leer %s (%s). Se usa lista vacía.", VERIFIED_JSON_PATH, e)
        return []


def save_verified_user(email: str) -> None:
    email = (email or "").strip().lower()
    if not email:
        return
    try:
        users = set(load_verified_users())
        if email not in users:
            users.add(email)
            VERIFIED_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(VERIFIED_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(sorted(users), f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Error guardando usuario verificado: %s", e)

# =========================================================
# Seguridad: CSRF + Rate Limiting
# =========================================================
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


_RATE_BUCKETS: Dict[str, List[float]] = {}


def rate_limit(max_calls: int, per_seconds: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "anon").split(",")[0]
            key = f"{ip}:{fn.__name__}"
            now = time.time()
            bucket = _RATE_BUCKETS.get(key, [])
            bucket = [t for t in bucket if now - t < per_seconds]
            if len(bucket) >= max_calls:
                return jsonify({"ok": False, "error": "Demasiadas solicitudes. Intenta más tarde."}), 429
            bucket.append(now)
            _RATE_BUCKETS[key] = bucket
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# =========================================================
# Render helper
# =========================================================
def try_render(template: str, status: int = 200, **ctx):
    """Renderiza con fallback a errores amigables y añade datos comunes."""
    ctx.setdefault("csrf_token", _get_csrf_token())
    try:
        return render_template(template, **ctx), status
    except TemplateNotFound:
        logger.error("Template no encontrado: %s", template)
        return render_template("errors/404.html", missing_template=template), 404
    except Exception as e:
        logger.exception("Error renderizando %s: %s", template, e)
        return render_template("errors/500.html", error=str(e)), 500

# =========================================================
# Health Check
# =========================================================
@main_bp.route("/healthz", methods=["GET"])
def healthz():
    try:
        firestore_db.collection("_healthz").document("ping").set(
            {"ts": datetime.utcnow().isoformat() + "Z"}
        )
        return jsonify({"ok": True, "service": "PlayTimeUY.main", "firebase": "ok"}), 200
    except Exception as e:
        logger.warning("Healthz firestore fallo: %s", e)
        return jsonify({"ok": False, "error": "firebase"}), 500

__all__ = [
    "main_bp",
    "logger",
    "firestore_db",
    "FIREBASE_REST_SIGNIN_URL",
    "DEFAULT_ROLE",
    "load_verified_users",
    "save_verified_user",
    "get_age",
    "is_minor",
    "csrf_protect",
    "rate_limit",
    "try_render",
]
