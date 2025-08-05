import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_admin import auth as admin_auth, firestore
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
import pyrebase
from urllib.parse import urlencode

# Cargar variables de entorno con python-dotenv (asegurate que esté instalado)
from dotenv import load_dotenv
load_dotenv()

main = Blueprint('main', __name__)

# Inicializar Firebase Admin SDK solo una vez
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
    })

db = firestore.client()

# Config Pyrebase (cliente)
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": "",
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": ""
}

firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()

# Google OAuth config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

import requests
import json

# ----------------------------
# RUTAS PRINCIPALES
# ----------------------------

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Leer formulario
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        dob = request.form.get('dob')
        country = request.form.get('country')
        twitter = request.form.get('twitter', '')
        instagram = request.form.get('instagram', '')
        role = request.form.get('role')

        # Validaciones básicas
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('main.register'))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for('main.register'))

        try:
            # Crear usuario con Pyrebase
            user = pyre_auth.create_user_with_email_and_password(email, password)
            uid = pyre_auth.get_account_info(user['idToken'])['users'][0]['localId']

            # Guardar info en Firestore
            db.collection('usuarios').document(uid).set({
                'full_name': full_name,
                'username': username,
                'email': email,
                'dob': dob,
                'country': country,
                'twitter': twitter,
                'instagram': instagram,
                'tipo': role,
                'fecha_creacion': datetime.utcnow(),
                'foto_perfil': '',
                'verificado': False
            })

            # Enviar email de verificación
            pyre_auth.send_email_verification(user['idToken'])

            flash("Cuenta creada con éxito. Verificá tu correo para activar la cuenta.", "success")
            return redirect(url_for('main.login'))
        except Exception as e:
            error_json = e.args[1] if len(e.args) > 1 else str(e)
            try:
                error_data = json.loads(error_json)
                error_message = error_data['error']['message']
            except Exception:
                error_message = str(e)
            flash(f"Error al crear cuenta: {error_message}", "danger")
            return redirect(url_for('main.register'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = pyre_auth.sign_in_with_email_and_password(email, password)
            user_info = pyre_auth.get_account_info(user['idToken'])['users'][0]

            if not user_info.get("emailVerified", False):
                flash("Verificá tu correo antes de iniciar sesión.", "warning")
                return redirect(url_for('main.verify_email'))

            uid = user_info['localId']
            doc = db.collection('usuarios').document(uid).get()
            if not doc.exists:
                flash("Usuario no registrado en base de datos.", "danger")
                return redirect(url_for('main.login'))

            user_data = doc.to_dict()
            session['user'] = {
                'uid': uid,
                'email': email,
                'tipo': user_data.get('tipo')
            }

            # Redirigir según rol
            tipo = user_data.get('tipo')
            if tipo == 'creator':
                return redirect(url_for('main.creator_panel'))
            elif tipo == 'buyer':
                return redirect(url_for('main.user_panel'))
            elif tipo == 'promoter':
                return redirect(url_for('main.reports_panel'))
            elif email == os.getenv("ADMIN_EMAIL"):
                return redirect(url_for('main.admin_dashboard'))
            else:
                flash("Rol de usuario desconocido.", "danger")
                return redirect(url_for('main.login'))
        except Exception as e:
            flash("Email o contraseña incorrectos.", "danger")
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/verify_email')
def verify_email():
    return render_template('verify_email.html')

@main.route('/logout')
def logout():
    session.pop('user', None)
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('main.login'))

# ----------------------------
# Google OAuth 2.0 (Registro/Login)
# ----------------------------

@main.route('/google_register')
def google_register():
    # Paso 1: Redirigir a Google para autorización
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    url = f"{google_auth_url}?{urlencode(params)}"
    return redirect(url)

@main.route('/callback')
def callback():
    # Paso 2: Google redirige aquí con código de autorización
    code = request.args.get('code')
    if not code:
        flash("Error en la autenticación con Google.", "danger")
        return redirect(url_for('main.login'))

    # Paso 3: Intercambiar código por token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    resp = requests.post(token_url, data=data)
    token_response = resp.json()
    access_token = token_response.get("access_token")
    id_token = token_response.get("id_token")

    if not access_token or not id_token:
        flash("No se pudo obtener el token de Google.", "danger")
        return redirect(url_for('main.login'))

    # Paso 4: Obtener info usuario de Google
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_resp = requests.get(userinfo_url, headers=headers)
    userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    full_name = userinfo.get("name")
    picture = userinfo.get("picture")

    if not email:
        flash("No se pudo obtener el correo de Google.", "danger")
        return redirect(url_for('main.login'))

    # Verificar si el usuario ya está en Firestore
    users_ref = db.collection('usuarios')
    docs = users_ref.where('email', '==', email).stream()
    existing_user = None
    for doc in docs:
        existing_user = doc
        break

    if existing_user:
        # Ya existe: loguear
        session['user'] = {
            'uid': existing_user.id,
            'email': email,
            'tipo': existing_user.to_dict().get('tipo')
        }
        flash(f"Bienvenido nuevamente {full_name}!", "success")
        return redirect(url_for('main.index'))
    else:
        # Nuevo usuario: crear con rol por defecto "buyer"
        new_doc = users_ref.document()
        new_doc.set({
            'full_name': full_name,
            'username': email.split('@')[0],
            'email': email,
            'dob': '',
            'country': '',
            'twitter': '',
            'instagram': '',
            'tipo': 'buyer',
            'fecha_creacion': datetime.utcnow(),
            'foto_perfil': picture or '',
            'verificado': True  # asume verificado por Google
        })

        session['user'] = {
            'uid': new_doc.id,
            'email': email,
            'tipo': 'buyer'
        }
        flash("Registro con Google exitoso.", "success")
        return redirect(url_for('main.index'))

# ----------------------------
# Rutas de paneles y páginas
# ----------------------------

@main.route('/creator_panel')
def creator_panel():
    if not session.get('user'):
        flash("Iniciá sesión para continuar.", "warning")
        return redirect(url_for('main.login'))
    return render_template('creator_panel.html')

@main.route('/user_panel')
def user_panel():
    if not session.get('user'):
        flash("Iniciá sesión para continuar.", "warning")
        return redirect(url_for('main.login'))
    return render_template('user_panel.html')

@main.route('/reports_panel')
def reports_panel():
    if not session.get('user'):
        flash("Iniciá sesión para continuar.", "warning")
        return redirect(url_for('main.login'))
    return render_template('reports.html')

@main.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('user'):
        flash("Iniciá sesión para continuar.", "warning")
        return redirect(url_for('main.login'))
    if session['user'].get('email') != os.getenv("ADMIN_EMAIL"):
        flash("Acceso denegado.", "danger")
        return redirect(url_for('main.index'))
    return render_template('admindashboard.html')

@main.route('/explorar')
def explorar():
    users_ref = db.collection('usuarios')
    docs = users_ref.where('tipo', '==', 'creator').stream()
    creators = []
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        creators.append(d)
    return render_template('explorar.html', creators=creators)

@main.route('/perfil/<username>')
def profile_view(username):
    users_ref = db.collection('usuarios').where('username', '==', username).limit(1).stream()
    user = next(users_ref, None)
    if user:
        user_data = user.to_dict()
        return render_template('profile.html', user=user_data)
    else:
        flash("Perfil no encontrado.", "warning")
        return redirect(url_for('main.explorar'))
