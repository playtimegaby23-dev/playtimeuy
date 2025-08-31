# app/routes/payments.py
import hmac
import hashlib
import json
from flask import Blueprint, request, current_app, jsonify
from datetime import datetime

bp = Blueprint("payments", __name__)

# --------------------------------------------------------
# Función para verificar la firma de Mercado Pago
# --------------------------------------------------------
def verify_mp_webhook(secret: str, payload: bytes, headers: dict) -> bool:
    """
    Valida la firma del webhook.
    Mercado Pago puede enviar 'x-mp-signature' o 'x-hook-signature'.
    """
    signature_header = headers.get("x-mp-signature") or headers.get("x-hook-signature")
    if not signature_header:
        current_app.logger.warning("Webhook recibido sin header de firma")
        return False
    # Calculamos HMAC-SHA256
    computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature_header)

# --------------------------------------------------------
# Endpoint de webhook de Mercado Pago
# --------------------------------------------------------
@bp.route("/webhooks/mercadopago", methods=["POST"])
def mercadopago_webhook():
    cfg = current_app.config
    raw_payload = request.get_data()
    headers = request.headers

    secret = cfg.get("MP_WEBHOOK_SECRET")
    if secret:
        if not verify_mp_webhook(secret, raw_payload, headers):
            current_app.logger.error("Webhook con firma inválida")
            return jsonify({"ok": False, "error": "Firma inválida"}), 403

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        current_app.logger.error(f"Webhook payload inválido: {e}")
        return jsonify({"ok": False, "error": "Payload inválido"}), 400

    # Logging básico de todos los webhooks recibidos
    event_type = payload.get("type") or payload.get("topic") or "unknown"
    resource = payload.get("data", {})
    timestamp = datetime.utcnow().isoformat()
    current_app.logger.info(f"[MP WEBHOOK] {timestamp} - Tipo: {event_type} - Payload: {json.dumps(resource)}")

    # --------------------------------------------------------
    # Manejo de eventos comunes (ejemplo: pagos, suscripciones, planes)
    # --------------------------------------------------------
    if event_type.startswith("payment") or event_type.startswith("payments"):
        # Aquí podrías actualizar tu DB con el pago recibido
        payment_id = resource.get("id") or resource.get("id_payment")
        current_app.logger.info(f"Pago recibido: {payment_id}")

    elif event_type.startswith("plan") or event_type.startswith("subscription"):
        subscription_id = resource.get("id")
        current_app.logger.info(f"Evento de suscripción/plan: {subscription_id}")

    # Agrega más eventos según tu lógica de negocio

    # Respuesta idempotente
    return jsonify({"ok": True, "received_at": timestamp}), 200
