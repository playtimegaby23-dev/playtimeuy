# app/main/user_routes.py
from __future__ import annotations

import os, hmac, hashlib, time
from typing import Any

from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from google.cloud import firestore

from app.config.firebase import firestore_db, firebase_storage
from app.main.main_routes import (
    get_current_user,
    login_required,
    csrf_protect,
    try_render,
    logger,
)

import mercadopago


# =========================================================
# Configuración de Mercado Pago
# =========================================================
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "").strip()
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "").strip()
MP = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None


# =========================================================
# Blueprint
# =========================================================
user_bp = Blueprint("user", __name__, url_prefix="/user")


# =========================================================
# Configuración de Archivos / Avatares
# =========================================================
ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE_MB: int = 5


def allowed_file(filename: str) -> bool:
    """Verifica que el archivo tenga una extensión válida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def filesize_ok(stream) -> bool:
    """Valida que el archivo no supere el tamaño máximo permitido (MB)."""
    try:
        pos = stream.tell()
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(pos)
        return size <= MAX_FILE_SIZE_MB * 1024 * 1024
    except Exception:
        return False


# =========================================================
# Rutas de Perfil
# =========================================================
@user_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    user = get_current_user()
    return try_render("users/profile.html", user=user)


@user_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
@csrf_protect
def profile_edit():
    """Editar perfil del usuario (username + avatar)."""
    user = get_current_user()

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        file = request.files.get("avatar")
        data: dict[str, Any] = {}

        if username:
            # Evita XSS y caracteres no permitidos
            safe_username = secure_filename(username)
            if safe_username != username:
                flash("El nombre contenía caracteres no válidos y fue saneado.", "info")
            data["username"] = safe_username

        if file and allowed_file(file.filename):
            if not filesize_ok(file.stream):
                flash(f"El archivo supera {MAX_FILE_SIZE_MB}MB.", "warning")
                return redirect(url_for("user.profile_edit"))

            filename = secure_filename(file.filename)
            blob_path = f"avatars/{user['uid']}/{int(time.time())}_{filename}"
            blob = firebase_storage.bucket().blob(blob_path)

            try:
                file.stream.seek(0)
                blob.upload_from_file(file, content_type=file.content_type)

                # Intentar URL pública, fallback con URL firmada (1 año)
                try:
                    blob.make_public()
                    data["avatar_url"] = blob.public_url
                except Exception:
                    data["avatar_url"] = blob.generate_signed_url(expiration=31536000)

            except Exception as exc:
                logger.exception("Error subiendo avatar: %s", exc)
                flash("No se pudo subir el avatar 😢", "danger")

        if data:
            try:
                firestore_db.collection("users").document(user["uid"]).update(data)
                user.update(data)
                session["user"] = user
                flash("Perfil actualizado correctamente ✅", "success")
            except Exception as exc:
                logger.exception("Error actualizando perfil Firestore: %s", exc)
                flash("No se pudo actualizar el perfil 😢", "danger")
        else:
            flash("No se detectaron cambios válidos ⚠️", "warning")

        return redirect(url_for("user.profile_edit"))

    return try_render("users/profile_edit.html", user=user)


# =========================================================
# Subcripciones del Creador
# =========================================================
@user_bp.route("/creator/subscriptions", methods=["GET"])
@login_required
def creator_subscriptions():
    user = get_current_user()
    subs = (
        firestore_db.collection("subscriptions")
        .where("creator_uid", "==", user["uid"])
        .stream()
    )
    return try_render(
        "creators/subscriptions.html", subscriptions=[doc.to_dict() for doc in subs]
    )


# =========================================================
# Historial de Pagos
# =========================================================
@user_bp.route("/payments/history", methods=["GET"])
@login_required
def payments_history():
    user = get_current_user()
    payments = (
        firestore_db.collection("payments")
        .where("buyer_uid", "==", user["uid"])
        .stream()
    )
    return try_render(
        "payments/history.html", payments=[doc.to_dict() for doc in payments]
    )


# =========================================================
# Crear Pago (Mercado Pago)
# =========================================================
@user_bp.route("/payment", methods=["POST"])
@login_required
@csrf_protect
def payment_create():
    """Crea una preferencia de pago en Mercado Pago."""
    if MP is None:
        return jsonify({"ok": False, "error": "Mercado Pago no configurado"}), 503

    user = get_current_user()
    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0

    creator_uid = (data.get("creator_uid") or "").strip()
    if amount <= 0 or not creator_uid:
        return jsonify({"ok": False, "error": "Datos inválidos"}), 400

    external_ref = f"playtimeuy_{user['uid']}_{int(time.time())}"

    preference_data = {
        "items": [
            {
                "title": "Contenido exclusivo",
                "quantity": 1,
                "unit_price": amount,
                "currency_id": "UYU",
            }
        ],
        "payer": {"email": user.get("email")},
        "back_urls": {
            "success": os.getenv("MP_SUCCESS_URL"),
            "failure": os.getenv("MP_FAILURE_URL"),
            "pending": os.getenv("MP_PENDING_URL"),
        },
        "auto_return": "approved",
        "external_reference": external_ref,
    }

    try:
        mp_resp = MP.preference().create(preference_data)
        pref_id = mp_resp.get("response", {}).get("id")
        if not pref_id:
            raise ValueError("No se recibió preference_id de MP")

        firestore_db.collection("payments").document(external_ref).set(
            {
                "external_reference": external_ref,
                "buyer_uid": user["uid"],
                "creator_uid": creator_uid,
                "amount": amount,
                "status": "pending",
                "preference_id": pref_id,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return jsonify({"ok": True, "preference_id": pref_id})

    except Exception as exc:
        logger.exception("Error creando preferencia MP: %s", exc)
        return jsonify({"ok": False, "error": "No se pudo crear la preferencia"}), 500


# =========================================================
# Webhook de Mercado Pago
# =========================================================
@user_bp.route("/payment/webhook", methods=["POST"])
def payment_webhook():
    """Webhook de notificaciones de Mercado Pago."""
    signature = (
        request.headers.get("X-Hub-Signature")
        or request.headers.get("x-signature")
        or ""
    )
    raw_body = request.get_data()

    if not MP_WEBHOOK_SECRET or not signature:
        logger.warning("Webhook recibido sin secret o firma")
        return jsonify({"ok": False}), 403

    computed = hmac.new(
        MP_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, signature):
        logger.warning("Webhook HMAC inválido")
        return jsonify({"ok": False}), 403

    data = request.get_json(silent=True) or {}
    external_ref = data.get("external_reference")
    status = data.get("status")

    # Caso directo: MP envía referencia + estado
    if external_ref and status:
        firestore_db.collection("payments").document(external_ref).update(
            {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
        )
        return jsonify({"ok": True})

    # Caso fallback: buscar por payment_id
    payment_id = data.get("data", {}).get("id") or data.get("id")
    if payment_id and MP:
        try:
            detail = MP.payment().get(payment_id)
            body = detail.get("response", {})
            external_ref = body.get("external_reference")
            status = body.get("status")
            if external_ref and status:
                firestore_db.collection("payments").document(external_ref).update(
                    {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
                )
                return jsonify({"ok": True})
        except Exception as exc:
            logger.exception("Error consultando pago MP %s: %s", payment_id, exc)

    return jsonify({"ok": True})
