"""
Blueprint 'mp_routes' de PlayTimeUY - Pagos y Webhook
- Creación de pagos con Mercado Pago
- Webhook HMAC-SHA256
- Historial de pagos
- Login Firebase REST (para routes.py)
"""

from __future__ import annotations
import os, hmac, hashlib, logging
from typing import Any, Dict, Optional, Tuple
import requests

from flask import Blueprint, request, jsonify, session

from app.config.firebase import firestore_db
import mercadopago

MP_ACCESS_TOKEN = (os.getenv("MP_ACCESS_TOKEN") or "").strip()
MP_WEBHOOK_SECRET = (os.getenv("MP_WEBHOOK_SECRET") or "").strip()
FIREBASE_WEB_API_KEY = (os.getenv("FIREBASE_WEB_API_KEY") or "").strip()

MP = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None
FIREBASE_REST_SIGNIN_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    if FIREBASE_WEB_API_KEY else None
)

mp_routes = Blueprint("mp_routes", __name__)

logger = logging.getLogger("PlayTimeUY.mp_routes")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------- Firebase Login ----------------
def _valid_email(email: str) -> bool:
    return bool(email and "@" in email and "." in email.rsplit("@", 1)[-1])

def firebase_login_password(email: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not FIREBASE_REST_SIGNIN_URL:
        logger.error("FIREBASE_WEB_API_KEY no configurada.")
        return None, "Login no disponible."
    if not _valid_email(email) or not password:
        return None, "Email o contraseña inválidos."
    try:
        resp = requests.post(FIREBASE_REST_SIGNIN_URL,
            json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
        data = resp.json()
        if resp.status_code != 200:
            logger.info("Login fallido %s: %s", email, data.get("error"))
            return None, "Usuario o contraseña incorrectos."
        uid = data.get("localId")
        if not uid:
            logger.error("Auth sin localId: %s", data)
            return None, "Respuesta inválida de autenticación."
        user_ref = firestore_db.collection("users").document(uid)
        snap = user_ref.get()
        if not snap.exists:
            minimal = {
                "uid": uid,
                "email": email,
                "username": data.get("displayName") or email.split("@")[0],
                "role": "buyer",
                "is_admin": False,
                "created_at": firestore_db.SERVER_TIMESTAMP if hasattr(firestore_db, "SERVER_TIMESTAMP") else None,
                "updated_at": firestore_db.SERVER_TIMESTAMP if hasattr(firestore_db, "SERVER_TIMESTAMP") else None,
            }
            user_ref.set(minimal)
            return minimal, None
        return snap.to_dict(), None
    except requests.RequestException as net_exc:
        logger.exception("Error de red autenticando Firebase: %s", net_exc)
        return None, "No se pudo conectar al servicio de autenticación."
    except Exception as exc:
        logger.exception("Error inesperado login Firebase: %s", exc)
        return None, "Error interno autenticando usuario."

# ---------------- Crear Pago ----------------
@mp_routes.route("/payment/create", methods=["POST"])
def create_payment():
    if not MP:
        return jsonify({"ok": False, "error": "Mercado Pago no configurado"}), 500
    data = request.get_json() or {}
    amount = data.get("amount")
    description = data.get("description") or "Compra PlayTimeUY"
    if not amount:
        return jsonify({"ok": False, "error": "Monto requerido"}), 400
    preference_data = {
        "items": [{"title": description, "quantity": 1, "unit_price": float(amount)}],
        "back_urls": {"success": "/", "failure": "/", "pending": "/"},
        "auto_return": "approved"
    }
    try:
        preference = MP.preference().create(preference_data)
        return jsonify({"ok": True, "preference": preference["response"]})
    except Exception as e:
        logger.exception("Error creando preferencia MP: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

# ---------------- Webhook ----------------
@mp_routes.route("/payment/webhook", methods=["POST"])
def mp_webhook():
    if not MP_WEBHOOK_SECRET:
        return "Webhook secret no configurado", 500
    sig = request.headers.get("X-Hub-Signature") or ""
    payload = request.data or b""
    expected_sig = hmac.new(MP_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        logger.warning("Webhook HMAC inválido")
        return "Invalid signature", 403
    try:
        data = request.get_json(force=True)
        logger.info("Webhook recibido: %s", data)
        return "OK", 200
    except Exception as e:
        logger.exception("Error procesando webhook: %s", e)
        return "Error interno", 500

# ---------------- Historial ----------------
@mp_routes.route("/payment/history", methods=["GET"])
def payment_history():
    user = session.get("user")
    if not user:
        return jsonify({"ok": False, "error": "No autenticado"}), 401
    uid = user.get("uid")
    try:
        docs = firestore_db.collection("payments").where("uid", "==", uid).stream()
        history = [doc.to_dict() for doc in docs]
        return jsonify({"ok": True, "payments": history})
    except Exception as e:
        logger.exception("Error obteniendo historial: %s", e)
        return jsonify({"ok": False, "error": "No se pudo obtener historial"}), 500
