# app/main/user_routes.py
from __future__ import annotations
import os, hmac, hashlib, time
from functools import wraps
from typing import Any, Dict

from flask import Blueprint, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

from app.config.firebase import firestore_db, firebase_storage
from app.main.main_routes import get_current_user, login_required, csrf_protect, try_render, logger
import mercadopago

# ---------------- Config / Init ----------------
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "").strip()
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "").strip()
MP = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None

user_bp = Blueprint("user", __name__, url_prefix="/user")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_FILE_SIZE_MB = 5

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _filesize_ok(stream) -> bool:
    try:
        pos = stream.tell()
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(pos)
        return size <= MAX_FILE_SIZE_MB * 1024 * 1024
    except Exception:
        return True

# ---------------- Profile Routes ----------------
@user_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    user = get_current_user()
    return try_render("users/profile.html", user=user)

@user_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
@csrf_protect
def profile_edit():
    user = get_current_user()
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        file = request.files.get("avatar")
        data: Dict[str, Any] = {}

        if username:
            data["username"] = username

        if file and allowed_file(file.filename):
            if not _filesize_ok(file.stream):
                flash(f"El archivo supera {MAX_FILE_SIZE_MB}MB.", "warning")
                return redirect(url_for("user.profile_edit"))

            filename = secure_filename(file.filename)
            blob_path = f"avatars/{user['uid']}/{int(time.time())}_{filename}"
            blob = firebase_storage.bucket().blob(blob_path)
            try:
                file.stream.seek(0)
            except Exception:
                pass
            blob.upload_from_file(file, content_type=file.content_type)
            try:
                blob.make_public()
                data["avatar_url"] = blob.public_url
            except Exception:
                data["avatar_url"] = blob.generate_signed_url(expiration=31536000)

        if data:
            firestore_db.collection("users").document(user["uid"]).update(data)
            user.update(data)
            session["user"] = user
            flash("Perfil actualizado", "success")
        else:
            flash("No se detectaron cambios válidos", "warning")

        return redirect(url_for("user.profile_edit"))

    return try_render("users/profile_edit.html", user=user)

# ---------------- Creator Subscriptions ----------------
@user_bp.route("/creator/subscriptions", methods=["GET"])
@login_required
def creator_subscriptions():
    user = get_current_user()
    subs_ref = firestore_db.collection("subscriptions").where("creator_uid", "==", user["uid"])
    subs = [doc.to_dict() for doc in subs_ref.stream()]
    return try_render("creators/subscriptions.html", subscriptions=subs)

# ---------------- Payments History ----------------
@user_bp.route("/payments/history", methods=["GET"])
@login_required
def payments_history():
    user = get_current_user()
    payments_ref = firestore_db.collection("payments").where("buyer_uid", "==", user["uid"])
    payments = [doc.to_dict() for doc in payments_ref.stream()]
    return try_render("payments/history.html", payments=payments)

# ---------------- Create Payment / Mercado Pago ----------------
@user_bp.route("/payment", methods=["POST"])
@login_required
@csrf_protect
def payment_create():
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
        "items": [{"title": "Contenido exclusivo", "quantity": 1, "unit_price": amount, "currency_id": "UYU"}],
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
        pref_id = mp_resp["response"]["id"]
        firestore_db.collection("payments").document(external_ref).set({
            "external_reference": external_ref,
            "buyer_uid": user["uid"],
            "creator_uid": creator_uid,
            "amount": amount,
            "status": "pending",
            "preference_id": pref_id,
            "created_at": firestore_db.SERVER_TIMESTAMP if hasattr(firestore_db, "SERVER_TIMESTAMP") else None,
        })
        return jsonify({"ok": True, "preference_id": pref_id})
    except Exception as exc:
        logger.exception("Error creando preferencia MP: %s", exc)
        return jsonify({"ok": False, "error": "No se pudo crear la preferencia"}), 500

# ---------------- Mercado Pago Webhook ----------------
@user_bp.route("/payment/webhook", methods=["POST"])
def payment_webhook():
    signature = request.headers.get("X-Hub-Signature") or request.headers.get("x-signature") or ""
    raw_body = request.get_data()

    if not MP_WEBHOOK_SECRET or not signature:
        logger.warning("Webhook recibido sin secret o firma")
        return jsonify({"ok": False}), 403

    computed = hmac.new(MP_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature):
        logger.warning("Webhook HMAC inválido")
        return jsonify({"ok": False}), 403

    data = request.get_json(silent=True) or {}
    external_ref = data.get("external_reference")
    status = data.get("status")

    if external_ref and status:
        firestore_db.collection("payments").document(external_ref).update({
            "status": status,
            "updated_at": firestore_db.SERVER_TIMESTAMP if hasattr(firestore_db, "SERVER_TIMESTAMP") else None
        })
        return jsonify({"ok": True})

    payment_id = data.get("data", {}).get("id") or data.get("id")
    if payment_id and MP:
        try:
            detail = MP.payment().get(payment_id)
            body = detail.get("response", {})
            external_ref = body.get("external_reference")
            status = body.get("status")
            if external_ref and status:
                firestore_db.collection("payments").document(external_ref).update({
                    "status": status,
                    "updated_at": firestore_db.SERVER_TIMESTAMP if hasattr(firestore_db, "SERVER_TIMESTAMP") else None
                })
                return jsonify({"ok": True})
        except Exception as exc:
            logger.exception("Error consultando pago MP %s: %s", payment_id, exc)

    return jsonify({"ok": True})
