from flask import render_template, request, redirect, flash, url_for, session
from app.firebase_init import pyre_auth
from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = pyre_auth.sign_in_with_email_and_password(email, password)
            session['user'] = user['localId']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'Error al iniciar sesión: {e}', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            pyre_auth.create_user_with_email_and_password(email, password)
            flash('Usuario registrado con éxito', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Error al registrar: {e}', 'danger')
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('main.index'))
