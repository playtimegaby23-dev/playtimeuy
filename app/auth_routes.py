# app/auth_routes.py
from __future__ import annotations
import os, json, re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
from firebase_admin import auth
import pyrebase
from app.config.firebase import pb_auth

auth_bp = Blueprint("auth", __name__)
USUARIOS_JSON = Path("data/usuarios.json")

def leer_usuarios_local() -> list:
    if not USUARIOS_JSON.exists():
        USUARIOS_JSON.parent.mkdir(parents=True, exist_ok=True)
        USUARIOS_JSON.write_text("[]")
    with USUARIOS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuario_local(user_data: dict):
    usuarios = leer_usuarios_local()
    usuarios.append(user_data)
    with USUARIOS_JSON.open("w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4)

def validar_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def validar_password(password: str) -> bool:
    return len(password) >= 6

def error_response(msg: str, code: int = 400):
    current_app.logger.warning(f"Auth Error {code}: {msg}")
    return jsonify({"ok": False, "error": msg}), code

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email y contraseña son requeridos")
    if not validar_email(email):
        return error_response("Formato de email inválido")
    if not validar_password(password):
        return error_response("La contraseña debe tener al menos 6 caracteres")

    try:
        user = auth.create_user(email=email, password=password)
        pb_user = pb_auth.create_user_with_email_and_password(email, password)
        pb_auth.send_email_verification(pb_user["idToken"])

        user_data = {
            "uid": user.uid,
            "email": email,
            "verified": False,
            "fecha_registro": datetime.utcnow().isoformat()
        }
        guardar_usuario_local(user_data)
        current_app.logger.info(f"Usuario registrado: {email}")
        return jsonify({"ok": True, "msg": "Usuario creado. Revisa tu correo para verificar la cuenta."}), 201
    except Exception as e:
        return error_response(f"Error al registrar usuario: {str(e)}", 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email y contraseña son requeridos")

    try:
        user = pb_auth.sign_in_with_email_and_password(email, password)
        info = pb_auth.get_account_info(user["idToken"])
        verified = info["users"][0].get("emailVerified", False)

        if not verified:
            return error_response("Debes verificar tu correo antes de iniciar sesión", 403)

        current_app.logger.info(f"Usuario logueado: {email}")
        return jsonify({"ok": True, "msg": "Login exitoso", "token": user["idToken"]}), 200
    except Exception:
        return error_response("Credenciales inválidas o usuario no existe", 401)
