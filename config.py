import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()

class Config:
    # 🔐 Clave secreta para sesiones Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_por_defecto_segura')

    # 🛠️ Modo Debug activado (desactiva en producción)
    DEBUG = True

    # 📁 Ruta a las credenciales del Admin SDK de Firebase
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        'GOOGLE_APPLICATION_CREDENTIALS',
        'C:/PlayTimeUY/secrets/playtimeuy-firebase-adminsdk-fbsvc-3f22ccce47.json'
    )

    # 🔥 Configuración de Firebase
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID')

    # 🔑 Configuración de Google Sign-In
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/callback')

    # 👑 Email del administrador del sitio
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
