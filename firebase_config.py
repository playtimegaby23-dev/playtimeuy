# firebase_config.py
"""
Configuración central de Firebase para toda la app.
Incluye:
- Firebase Admin SDK (Firestore y Storage)
- Pyrebase (Auth y Storage)
"""

import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

# ------------------- CARGA DE VARIABLES DE ENTORNO -------------------
load_dotenv()

# ------------------- VALIDACIÓN DE VARIABLES OBLIGATORIAS -------------------
required_env_vars = [
    "GOOGLE_APPLICATION_CREDENTIALS",
    "FIREBASE_API_KEY",
    "FIREBASE_AUTH_DOMAIN",
    "FIREBASE_PROJECT_ID",
    "FIREBASE_STORAGE_BUCKET",
    "FIREBASE_MESSAGING_SENDER_ID",
    "FIREBASE_APP_ID"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Faltan variables de entorno: {', '.join(missing_vars)}")

# ------------------- RUTA DE CREDENCIALES Y ADMIN SDK -------------------
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Archivo de credenciales no encontrado: {cred_path}")

# Inicializa Firebase Admin solo si no está inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
    })

# Cliente Firestore (Admin SDK)
db = firestore.client()

# ------------------- CONFIGURACIÓN PYREBASE -------------------
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "")
}

firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()       # 🔹 Autenticación
pyre_storage = firebase.storage() # 🔹 Storage

# ------------------- EXPORTACIÓN DE OBJETOS CLAVE -------------------
__all__ = ["db", "firebase_config", "pyre_auth", "pyre_storage"]

# ------------------- FUNCIÓN DE DEPURACIÓN OPCIONAL -------------------
def debug_firebase():
    """Muestra el estado de las instancias de Firebase."""
    print("Firebase Admin SDK inicializado:", bool(firebase_admin._apps))
    print("Firestore:", bool(db))
    print("Pyrebase Auth:", bool(pyre_auth))
    print("Pyrebase Storage:", bool(pyre_storage))
