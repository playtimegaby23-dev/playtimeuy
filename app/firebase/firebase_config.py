import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener rutas y claves desde variables de entorno
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
firebase_api_key = os.getenv("FIREBASE_API_KEY")

# Validar existencia de archivo de credenciales
if not cred_path or not os.path.isfile(cred_path):
    raise FileNotFoundError(
        f"No se encontró el archivo de credenciales en: {cred_path}.\n"
        f"Verificá que la variable GOOGLE_APPLICATION_CREDENTIALS esté bien configurada en tu archivo .env"
    )

# Inicializar Firebase Admin SDK (una sola vez)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        "storageBucket": "playtimeuy.appspot.com"
    })

# Cliente de Firestore para acceso administrativo
db = firestore.client()

# Configuración para Pyrebase (autenticación de usuarios)
firebase_config = {
    "apiKey": firebase_api_key,
    "authDomain": "playtimeuy.firebaseapp.com",
    "projectId": "playtimeuy",
    "storageBucket": "playtimeuy.appspot.com",
    "messagingSenderId": "709385694606",
    "appId": "1:709385694606:web:7e6ff7ff52bcaba9cf48df",
    "databaseURL": "",  # Usalo solo si estás con Realtime DB
    "measurementId": ""  # Opcional
}

# Inicializar Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()
pyre_storage = firebase.storage()

# Exportar para otros módulos
__all__ = ["db", "firebase_config", "pyre_auth", "pyre_storage"]
