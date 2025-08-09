# firebase_config.py
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Cargar variables de entorno desde .env
load_dotenv()

# Ruta de credenciales de Firebase Admin SDK
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError(
        f"Archivo de credenciales de Firebase no encontrado: {cred_path}"
    )

# Inicializar Firebase Admin SDK (solo una vez)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "playtimeuy.appspot.com")
    })

# Cliente Firestore (Admin SDK)
db = firestore.client()

# Configuración Pyrebase para autenticación y storage
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "playtimeuy.firebaseapp.com"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "playtimeuy"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "playtimeuy.appspot.com"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "")
}

firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()
pyre_storage = firebase.storage()

# Exportar objetos clave
__all__ = ["db", "firebase_config", "pyre_auth", "pyre_storage"]
