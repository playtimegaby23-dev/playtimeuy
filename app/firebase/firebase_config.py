import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Cargar variables de entorno desde .env
load_dotenv()

# Leer variables del .env
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
firebase_api_key = os.getenv("FIREBASE_API_KEY")

if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError("El archivo de credenciales de Firebase no fue encontrado. Verificá tu .env.")

# Inicializar Firebase Admin SDK (una sola vez)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'playtimeuy.appspot.com'
    })

# Cliente Firestore (Admin SDK)
db = firestore.client()

# Configuración Pyrebase (autenticación cliente)
firebase_config = {
    "apiKey": firebase_api_key,
    "authDomain": "playtimeuy.firebaseapp.com",
    "databaseURL": "",  # Solo si usás Realtime DB
    "projectId": "playtimeuy",
    "storageBucket": "playtimeuy.appspot.com",
    "messagingSenderId": "709385694606",
    "appId": "1:709385694606:web:7e6ff7ff52bcaba9cf48df",
    "measurementId": ""  # Opcional
}

# Inicializar Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()
pyre_storage = firebase.storage()

# Exportar objetos clave
__all__ = ["db", "firebase_config", "pyre_auth", "pyre_storage"]
