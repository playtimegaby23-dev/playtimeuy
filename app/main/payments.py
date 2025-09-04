"""
Blueprint 'mp_routes' de PlayTimeUY - Pagos y Webhook
✅ Creación de pagos con Mercado Pago (Checkout Pro)
✅ Webhook seguro con HMAC-SHA256
✅ Historial de pagos en Firestore
✅ Login Firebase REST (fallback para routes.py)
✅ Logs estructurados + manejo de errores robusto
"""

from __future__ import annotations
import os, hmac, hashlib, logging
from typing import Any, Dict, Optional, Tuple
import requests

from flask import Blueprint, request, jsonify, session
from google.cloud.firestore import Client as FirestoreClient
import mercadopago

from app.config.firebase import firestore_db  # Firestore inicializado en config

# =========================================================
# Configuración
# =========================================================
MP_ACCESS_TOKEN = (os.getenv("MP_ACCESS_TOKEN") or "").strip()
MP_WEBHOOK_SECRET = (os.getenv("MP_WEBHOOK_SECRET") or "").strip()
FIREBASE_WEB_API_KEY = (os.getenv("FIREBASE_WEB_API_KEY") or "").strip()

MP = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None
FIREBASE_REST_SIGNIN_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    if FIREBASE_WEB_API_KEY else None
)

mp_routes = Blueprint("mp_routes", __name__)

# =========================================================
# Logger
# =========================================================
logger = logging.getLogger("PlayTimeUY.mp_routes")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# =========================================================
# Firebase Login (REST)
# =========================================================
def _valid_email(email: str) -> bool:
    return bool(email and "@" in email and "." in email.rsplit("@", 1)[-1])

def firebase_login_password(
    email: str, password: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Login simple vía Firebase REST"""
    if not FIREBASE_REST_SIGNIN_URL:
        return None, "Login no disponible (API key faltante)."
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
            logger.info("Login fallido %s: %s", email, data.get("error"))
            return None, "Usuario o contraseña incorrectos."

        uid = data.get("localId")
        if not uid:
            logger.error("Respuesta inválida de Firebase Auth: %s", data)
            return None, "Error autenticando usuario."

        # Crear usuario mínimo en Firestore si no existe
        user_ref = firestore_db.collection("users").document(uid)
        snap = user_ref.get()
        if not snap.exists:
            minimal = {
                "uid": uid,
                "email": email,
                "username": data.get("displayName") or email.split("@")[0],
                "role": "buyer",
                "is_admin": False,
                "created_at": firestore_db.field_path.SERVER_TIMESTAMP,  # Marca temporal
                "updated_at": firestore_db.field_path.SERVER_TIMESTAMP,
            }
            user_ref.set(minimal)
            return minimal, None

        return snap.to_dict(), None

    except requests.RequestException as net_exc:
        logger.exception("Error de red autenticando Firebase")
        return None, "No se pudo conectar a Firebase."
    except Exception as exc:
        logger.exception("Error inesperado en login Firebase")
        return None, "Error interno autenticando usuario."

# =========================================================
# Crear Pago (Checkout Pro)
# =========================================================
@mp_routes.route("/payment/create", methods=["POST"])
def create_payment():
    if not MP:
        return jsonify({"ok": False, "error": "Mercado Pago no configurado"}), 500

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")
    description = data.get("description") or "Compra PlayTimeUY"

    if not amount or not isinstance(amount, (int, float)):
        return jsonify({"ok": False, "error": "Monto inválido"}), 400

    preference_data = {
        "items": [{"title": description, "quantity": 1, "unit_price": float(amount)}],
        "back_urls": {
            "success": "https://playtimeuy.com/checkout/success",
            "failure": "https://playtimeuy.com/checkout/failure",
            "pending": "https://playtimeuy.com/checkout/pending",
        },
        "auto_return": "approved",
        "binary_mode": True,  # Pago aprobado o rechazado
        "external_reference": f"PTUY-{os.urandom(6).hex()}",  # ID único
    }

    try:
        preference = MP.preference().create(preference_data)
        logger.info("Preferencia creada: %s", preference["response"].get("id"))
        return jsonify({"ok": True, "preference": preference["response"]})
    except Exception as e:
        logger.exception("Error creando preferencia MP")
        return jsonify({"ok": False, "error": "Error al generar el pago"}), 500

# =========================================================
# Webhook (HMAC-SHA256)
# =========================================================
@mp_routes.route("/payment/webhook", methods=["POST"])
def mp_webhook():
    if not MP_WEBHOOK_SECRET:
        return "Webhook secret no configurado", 500

    sig = request.headers.get("X-Hub-Signature") or ""
    payload = request.data or b""

    expected_sig = hmac.new(
        MP_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        logger.warning("Webhook HMAC inválido")
        return "Invalid signature", 403

    try:
        data = request.get_json(force=True)
        logger.info("Webhook recibido: %s", data)

        # Guardar en Firestore (colección 'webhooks')
        firestore_db.collection("webhooks").add({
            "data": data,
            "received_at": firestore_db.field_path.SERVER_TIMESTAMP,
        })

        return "OK", 200
    except Exception as e:
        logger.exception("Error procesando webhook")
        return "Error interno", 500

# =========================================================
# Historial de Pagos
# =========================================================
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
    except Exception:
        logger.exception("Error obteniendo historial de pagos")
        return jsonify({"ok": False, "error": "No se pudo obtener historial"}), 500
