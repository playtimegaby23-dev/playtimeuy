# app/auth_routes.py
from __future__ import annotations
import os
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from firebase_admin import auth
from app.config.firebase import pb_auth  # Pyrebase auth instance

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Archivo local opcional para usuarios
USUARIOS_JSON = Path("data/usuarios.json")

# -------------------------
# Utilidades locales
# -------------------------
def leer_usuarios_local() -> list:
    """Lee usuarios desde JSON local; crea archivo si no existe."""
    if not USUARIOS_JSON.exists():
        USUARIOS_JSON.parent.mkdir(parents=True, exist_ok=True)
        USUARIOS_JSON.write_text("[]")
    with USUARIOS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuario_local(user_data: dict):
    """Guarda usuario en JSON local."""
    usuarios = leer_usuarios_local()
    # Evitar duplicados por email
    if not any(u.get("email") == user_data.get("email") for u in usuarios):
        usuarios.append(user_data)
        with USUARIOS_JSON.open("w", encoding="utf-8") as f:
            json.dump(usuarios, f, indent=4, ensure_ascii=False)

def validar_email(email: str) -> bool:
    """Valida formato de email simple."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def validar_password(password: str) -> bool:
    """Valida contraseña mínima 6 caracteres."""
    return bool(password) and len(password) >= 6

def error_response(msg: str, code: int = 400):
    """Respuesta JSON consistente para errores."""
    current_app.logger.warning(f"[Auth Error {code}] {msg}")
    return jsonify({"ok": False, "error": msg}), code

# -------------------------
# Rutas
# -------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    """Registro de usuario con Firebase Admin + Pyrebase."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return error_response("Email y contraseña son requeridos")
    if not validar_email(email):
        return error_response("Formato de email inválido")
    if not validar_password(password):
        return error_response("La contraseña debe tener al menos 6 caracteres")

    try:
        # Firebase Admin
        fb_user = auth.create_user(email=email, password=password)
        # Pyrebase (para verificación de email)
        pb_user = pb_auth.create_user_with_email_and_password(email, password)
        pb_auth.send_email_verification(pb_user["idToken"])

        # Guardar localmente
        user_data = {
            "uid": fb_user.uid,
            "email": email,
            "verified": False,
            "fecha_registro": datetime.utcnow().isoformat()
        }
        guardar_usuario_local(user_data)

        current_app.logger.info(f"[Auth] Usuario registrado: {email}")
        return jsonify({"ok": True, "msg": "Usuario creado. Revisa tu correo para verificar la cuenta."}), 201
    except Exception as e:
        current_app.logger.exception(f"[Auth] Error registrando usuario: {email}")
        return error_response(f"Error al registrar usuario: {str(e)}", 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login de usuario con verificación de email."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return error_response("Email y contraseña son requeridos")

    try:
        pb_user = pb_auth.sign_in_with_email_and_password(email, password)
        account_info = pb_auth.get_account_info(pb_user["idToken"])
        verified = account_info["users"][0].get("emailVerified", False)

        if not verified:
            return error_response("Debes verificar tu correo antes de iniciar sesión", 403)

        current_app.logger.info(f"[Auth] Usuario logueado: {email}")
        return jsonify({
            "ok": True,
            "msg": "Login exitoso",
            "token": pb_user["idToken"],
            "email": email
        }), 200
    except Exception as e:
        current_app.logger.warning(f"[Auth] Login fallido: {email} ({str(e)})")
        return error_response("Credenciales inválidas o usuario no existe", 401)
