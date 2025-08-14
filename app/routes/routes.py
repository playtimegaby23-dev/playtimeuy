from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import re
from firebase_config import auth, db  # Importa tu configuración inicializada

main = Blueprint('main', __name__)

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


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
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        dob = request.form.get('dob', '').strip()
        country = request.form.get('country', '').strip()
        twitter = request.form.get('twitter', '').strip()
        instagram = request.form.get('instagram', '').strip()
        role = request.form.get('role', '').strip()

        if not all([full_name, username, email, password, confirm_password, dob, country, role]):
            flash("Por favor, completa todos los campos obligatorios.", "danger")
            return redirect(url_for('main.register'))

        if not EMAIL_REGEX.match(email):
            flash("Correo electrónico inválido.", "danger")
            return redirect(url_for('main.register'))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for('main.register'))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('main.register'))

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            user_id = user['localId']

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
                "verificado": False
            })

            flash("Registro exitoso. Verifica tu correo para activar la cuenta.", "success")
            return redirect(url_for('main.login'))

        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                flash("Este correo ya está registrado.", "danger")
            elif "WEAK_PASSWORD" in error_msg:
                flash("La contraseña es muy débil.", "danger")
            else:
                flash("Ocurrió un error al registrar. Intenta nuevamente.", "danger")

    return render_template('register.html')


# ------------------- LOGIN -------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_info = auth.get_account_info(user['idToken'])['users'][0]

            if not user_info.get("emailVerified", False):
                flash("Debes verificar tu correo antes de iniciar sesión.", "warning")
                return redirect(url_for('main.login'))

            session['user'] = {
                "id": user_info['localId'],
                "email": user_info['email']
            }

            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            error_msg = str(e)
            if "INVALID_PASSWORD" in error_msg:
                flash("Contraseña incorrecta.", "danger")
            elif "EMAIL_NOT_FOUND" in error_msg:
                flash("No existe una cuenta con ese correo.", "danger")
            else:
                flash("Error al iniciar sesión. Intenta nuevamente.", "danger")

    return render_template('login.html')


# ------------------- DASHBOARD (Privado) -------------------
@main.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "warning")
        return redirect(url_for('main.login'))

    user_id = session['user']['id']
    user_data = db.collection('usuarios').document(user_id).get()

    if not user_data.exists:
        flash("No se encontraron datos del usuario.", "danger")
        return redirect(url_for('main.logout'))

    return render_template('dashboard.html', user=user_data.to_dict())


# ------------------- LOGOUT -------------------
@main.route('/logout')
def logout():
    session.pop('user', None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('main.home'))
