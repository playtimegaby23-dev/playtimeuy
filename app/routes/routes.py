# main/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
from functools import wraps
import re

# Pyrebase (cliente) y Firestore (Admin) salidos de tu config
from firebase_config import auth as pyrebase_auth, db  # <-- Pyrebase auth + Firestore client

# Firebase Admin para verificar ID Tokens de Google
from firebase_admin import auth as admin_auth

main = Blueprint('main', __name__)

# ------------------- CONFIG / CONSTANTES -------------------
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


# ------------------- HELPERS -------------------
def login_required(view_func):
    """Protege rutas que requieren sesión abierta."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            flash("Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapped


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_REGEX.match(email))


def parse_pyrebase_error(err: Exception) -> str:
    """
    Intenta mapear errores comunes de Pyrebase para mostrar mensajes claros.
    """
    s = str(err)
    # Errores frecuentes devueltos por la REST API de Firebase Identity Toolkit
    if "EMAIL_EXISTS" in s:
        return "Este correo ya está registrado."
    if "WEAK_PASSWORD" in s or "Password should be at least" in s:
        return "La contraseña es demasiado débil (mínimo 6 caracteres)."
    if "INVALID_PASSWORD" in s:
        return "Contraseña incorrecta."
    if "EMAIL_NOT_FOUND" in s:
        return "No existe una cuenta con ese correo."
    if "USER_DISABLED" in s:
        return "La cuenta está deshabilitada."
    if "TOO_MANY_ATTEMPTS_TRY_LATER" in s:
        return "Demasiados intentos. Intenta más tarde."
    if "INVALID_ID_TOKEN" in s:
        return "Token inválido. Vuelve a intentarlo."
    return "Ocurrió un error. Intenta nuevamente."


def set_session(user_id: str, email: str):
    """
    Guarda datos mínimos en sesión. Ajusta aquí lo que quieras persistir.
    """
    session['user'] = {
        "id": user_id,
        "email": email,
    }
    # Haz la sesión persistente por 7 días si querés “Recordarme”
    session.permanent = True


# ------------------- PÁGINA PRINCIPAL -------------------
@main.route("/")
def home():
    return render_template("index.html")


# ------------------- REGISTRO -------------------
@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        dob = request.form.get('dob', '').strip()
        country = request.form.get('country', '').strip()
        twitter = request.form.get('twitter', '').strip()
        instagram = request.form.get('instagram', '').strip()
        role = request.form.get('role', '').strip()

        # Validaciones básicas
        if not all([full_name, username, email, password, confirm_password, dob, country, role]):
            flash("Por favor, completa todos los campos obligatorios.", "danger")
            return redirect(url_for('main.register'))

        if not is_valid_email(email):
            flash("Correo electrónico inválido.", "danger")
            return redirect(url_for('main.register'))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for('main.register'))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('main.register'))

        try:
            # Crear usuario en Firebase Authentication (Pyrebase)
            user = pyrebase_auth.create_user_with_email_and_password(email, password)

            # Enviar verificación por email
            pyrebase_auth.send_email_verification(user['idToken'])

            user_id = user['localId']

            # Guardar datos del usuario en Firestore
            db.collection('usuarios').document(user_id).set({
                "full_name": full_name,
                "username": username,
                "email": email,
                "dob": dob,
                "country": country,
                "twitter": twitter,
                "instagram": instagram,
                "role": role,
                "fecha_registro": datetime.utcnow(),
                "verificado": False,
                "auth_provider": "password"
            })

            flash("Registro exitoso. Verifica tu correo para activar la cuenta.", "success")
            return redirect(url_for('main.login'))

        except Exception as e:
            flash(parse_pyrebase_error(e), "danger")

    return render_template('register.html')


# ------------------- LOGIN (Email & Password) -------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not is_valid_email(email):
            flash("Correo electrónico inválido.", "danger")
            return redirect(url_for('main.login'))

        if not password:
            flash("Debes ingresar la contraseña.", "danger")
            return redirect(url_for('main.login'))

        try:
            # Autenticar con Pyrebase
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)

            # Verificar si el email está verificado
            user_info = pyrebase_auth.get_account_info(user['idToken'])['users'][0]
            if not user_info.get("emailVerified", False):
                flash("Debes verificar tu correo antes de iniciar sesión.", "warning")
                return redirect(url_for('main.login'))

            user_id = user_info['localId']

            # (Opcional) Sincronizar verificado en Firestore
            db.collection('usuarios').document(user_id).set({"verificado": True}, merge=True)

            # Guardar sesión
            set_session(user_id, email)

            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            flash(parse_pyrebase_error(e), "danger")

    return render_template('login.html')


# ------------------- LOGIN con Google (desde botón del frontend) -------------------
@main.route('/login/google', methods=['POST'])
def login_google():
    """
    El frontend obtiene el idToken con Firebase Web SDK (signInWithPopup)
    y lo envía aquí en JSON: { "idToken": "<token>" }.
    Validamos el token con Firebase Admin, creamos/actualizamos en Firestore,
    y respondemos con la URL de redirección para que el frontend navegue.
    """
    try:
        data = request.get_json(silent=True) or {}
        id_token = data.get("idToken")
        if not id_token:
            return jsonify({"error": "Falta idToken"}), 400

        # Verificar token con Admin SDK (seguro, desde servidor)
        decoded = admin_auth.verify_id_token(id_token)
        uid = decoded.get("uid")
        email = (decoded.get("email") or "").lower()

        if not uid or not email:
            return jsonify({"error": "Token inválido"}), 400

        # Crear/actualizar usuario en Firestore
        user_ref = db.collection('usuarios').document(uid)
        snap = user_ref.get()

        base_data = {
            "email": email,
            "verificado": True,            # Google siempre viene verificado
            "auth_provider": "google",
            "ultima_sesion": datetime.utcnow()
        }

        if not snap.exists:
            user_ref.set({
                **base_data,
                "fecha_registro": datetime.utcnow()
            }, merge=True)
        else:
            user_ref.set(base_data, merge=True)

        # Abrir sesión
        set_session(uid, email)

        # Devolvemos JSON con la URL a donde redirigir
        return jsonify({"redirect": url_for("main.dashboard")})

    except Exception as e:
        # No exponemos detalles internos al cliente
        print("Google login error:", e)
        return jsonify({"error": "Google Sign-In failed"}), 400


# ------------------- RESET PASSWORD -------------------
@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not is_valid_email(email):
            flash("Correo electrónico inválido.", "danger")
            return redirect(url_for('main.forgot_password'))
        try:
            pyrebase_auth.send_password_reset_email(email)
            flash("Te enviamos un email para restablecer tu contraseña.", "success")
            return redirect(url_for('main.login'))
        except Exception as e:
            flash(parse_pyrebase_error(e), "danger")

    return render_template('forgot_password.html')


# ------------------- DASHBOARD (Privado) -------------------
@main.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user']['id']
    user_doc = db.collection('usuarios').document(user_id).get()

    if not user_doc.exists:
        # Si no encontramos datos, cerramos sesión para evitar estados inconsistentes
        session.pop('user', None)
        flash("No se encontraron datos del usuario.", "danger")
        return redirect(url_for('main.login'))

    return render_template('dashboard.html', user=user_doc.to_dict())


# ------------------- LOGOUT -------------------
@main.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('main.home'))
