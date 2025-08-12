from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import re

main = Blueprint('main', __name__)

# Firebase imports y config ya deberían estar inicializados antes y accesibles aquí
# auth = pyrebase auth
# db = firestore client

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Obtener datos del formulario
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

        # Validaciones básicas
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

        # Aquí puedes agregar validaciones extra como username único, fecha válida, etc.

        try:
            # Crear usuario en Firebase Auth
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            user_id = user['localId']

            # Guardar datos en Firestore
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
