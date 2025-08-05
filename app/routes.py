from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_admin import auth as admin_auth, firestore
from datetime import datetime
import pyrebase
import os
import firebase_admin
from firebase_admin import credentials

main = Blueprint('main', __name__)

# Firebase Admin SDK
cred = credentials.Certificate(os.path.join(os.getcwd(), 'secrets', 'playtimeuy-firebase-adminsdk-fbsvc-0052daa66e.json'))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Pyrebase config
firebase_config = {
    "apiKey": "AIzaSyC3fB1L-ZYElshW9v9aPVtOr94T2YSHszU",
    "authDomain": "playtimeuy.firebaseapp.com",
    "projectId": "playtimeuy",
    "storageBucket": "playtimeuy.appspot.com",
    "messagingSenderId": "709385694606",
    "appId": "1:709385694606:web:2e67ef1e57cb70306158ae",
    "measurementId": "G-LE3M70LM6E",
    "databaseURL": "https://playtimeuy.firebaseio.com"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
storage = firebase.storage()

# Home
@main.route('/')
def index():
    return render_template('index.html')

# Página de exploración de creadores
@main.route('/explorar')
def explorar():
    usuarios = db.collection('usuarios').stream()
    lista = [user.to_dict() for user in usuarios if user.to_dict().get('tipo') == 'creador']
    return render_template('explorar.html', creadores=lista)

# Página de perfil público del creador
@main.route('/perfil/<string:user_id>')
def perfil_creador(user_id):
    user_doc = db.collection('usuarios').document(user_id).get()
    if user_doc.exists:
        creador = user_doc.to_dict()
        return render_template('perfil_creador.html', creador=creador)
    else:
        flash('Creador no encontrado.', 'error')
        return redirect(url_for('main.explorar'))

# Registro de usuario
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        tipo = request.form['tipo']  # creador, comprador, promotor

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            user_id = user['localId']
            user_data = {
                'nombre': nombre,
                'email': email,
                'tipo': tipo,
                'fecha_registro': datetime.now(),
                'verificado': False,
                'foto': '',
                'bio': '',
                'redes': {}
            }
            db.collection('usuarios').document(user_id).set(user_data)
            flash('Registro exitoso. Verifica tu email antes de iniciar sesión.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('main.register'))
    return render_template('auth/register.html')

# Inicio de sesión
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_info = auth.get_account_info(user['idToken'])
            email_verified = user_info['users'][0]['emailVerified']

            if not email_verified:
                flash('Debes verificar tu correo electrónico antes de iniciar sesión.', 'error')
                return redirect(url_for('main.login'))

            user_id = user['localId']
            user_doc = db.collection('usuarios').document(user_id).get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                session['user_id'] = user_id
                session['email'] = email
                session['tipo'] = user_data['tipo']

                if email == 'playtimegaby23@gmail.com':
                    return redirect(url_for('main.admin_dashboard'))
                elif user_data['tipo'] == 'creador':
                    return redirect(url_for('main.dashboard_creador'))
                elif user_data['tipo'] == 'comprador':
                    return redirect(url_for('main.dashboard_comprador'))
                elif user_data['tipo'] == 'promotor':
                    return redirect(url_for('main.dashboard_promotor'))
                else:
                    return redirect(url_for('main.index'))
        except Exception as e:
            flash('Credenciales inválidas o error de autenticación.', 'error')
            return redirect(url_for('main.login'))

    return render_template('auth/login.html')

# Dashboards
@main.route('/dashboard/creador')
def dashboard_creador():
    if session.get('tipo') != 'creador':
        return redirect(url_for('main.login'))
    return render_template('dashboards/creador.html')

@main.route('/dashboard/comprador')
def dashboard_comprador():
    if session.get('tipo') != 'comprador':
        return redirect(url_for('main.login'))
    return render_template('dashboards/comprador.html')

@main.route('/dashboard/promotor')
def dashboard_promotor():
    if session.get('tipo') != 'promotor':
        return redirect(url_for('main.login'))
    return render_template('dashboards/promotor.html')

# Panel del administrador
@main.route('/admin')
def admin_dashboard():
    if session.get('email') != 'playtimegaby23@gmail.com':
        return redirect(url_for('main.login'))
    return render_template('admin/dashboard.html')

# Cerrar sesión
@main.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('main.index'))

# Página de error 404
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
