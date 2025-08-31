# app/config/firebase.py
"""
Configuración y inicialización de Firebase para PlayTimeUY v3.0
---------------------------------------------------------------
✅ Admin SDK (Auth, Firestore, Realtime DB, Storage)
✅ Pyrebase para frontend auth
✅ Manejo seguro si faltan credenciales
✅ Logging profesional
✅ Reutilización de instancia (singleton)
"""

from __future__ import annotations
import os
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore, db, storage
import pyrebase

# =========================================================
# Rutas y carga de env
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

logger = logging.getLogger("PlayTimeUY.firebase")

# =========================================================
# Resolver credenciales Firebase Admin
# =========================================================
DEFAULT_SERVICE_ACCOUNT = BASE_DIR / "secrets" / "playtimeuy-firebase-adminsdk-fbsvc-59c2e483cb.json"

firebase_app: firebase_admin.App | None = None
cred: credentials.Certificate | None = None

try:
    # JSON completo en variable de entorno
    if os.getenv("FIREBASE_CREDENTIALS_JSON"):
        cred_dict = json.loads(os.getenv("FIREBASE_CREDENTIALS_JSON"))
        cred = credentials.Certificate(cred_dict)
        logger.info("🔹 Credenciales Firebase cargadas desde variable de entorno JSON")
    else:
        # Ruta a archivo (env o default)
        service_account_path = Path(
            os.getenv("FIREBASE_SERVICE_ACCOUNT", str(DEFAULT_SERVICE_ACCOUNT))
        )
        if not service_account_path.exists():
            logger.warning("⚠️ Service Account no encontrado en: %s", service_account_path)
        else:
            cred = credentials.Certificate(str(service_account_path))
            logger.info("🔹 Service Account Firebase cargado desde: %s", service_account_path)

    # =====================================================
    # Inicializar Firebase Admin
    # =====================================================
    if cred:
        if not firebase_admin._apps:
            firebase_app = firebase_admin.initialize_app(
                cred,
                options={
                    "databaseURL": os.getenv(
                        "FIREBASE_DATABASE_URL",
                        "https://playtimeuy-default-rtdb.firebaseio.com",
                    ),
                    "storageBucket": os.getenv(
                        "FIREBASE_STORAGE_BUCKET",
                        "playtimeuy.appspot.com",
                    ),
                },
            )
            logger.info("✅ Firebase Admin inicializado correctamente (Proyecto: %s)", cred.project_id)
        else:
            firebase_app = firebase_admin.get_app()
            logger.info("♻️ Firebase Admin ya estaba inicializado, reutilizando instancia")
    else:
        logger.warning("⚠️ Firebase Admin no inicializado: credenciales inválidas")

except Exception as e:
    logger.exception("❌ Error inicializando Firebase Admin: %s", e)
    firebase_app = None

# =========================================================
# Servicios exportados (con fallback seguro)
# =========================================================
try:
    firebase_auth = auth if firebase_app else None
except Exception:
    firebase_auth = None
    logger.warning("⚠️ Firebase Auth no disponible")

try:
    firestore_db = firestore.client() if firebase_app else None
except Exception:
    firestore_db = None
    logger.warning("⚠️ Firestore no disponible")

try:
    realtime_db = db.reference("/") if firebase_app else None
except Exception:
    realtime_db = None
    logger.warning("⚠️ Realtime DB no disponible")

try:
    firebase_storage = storage.bucket() if firebase_app else None
except Exception:
    firebase_storage = None
    logger.warning("⚠️ Firebase Storage no disponible")

# =========================================================
# Inicialización Pyrebase (Frontend)
# =========================================================
firebase_config = {
    "apiKey": os.getenv("VITE_FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("VITE_FIREBASE_AUTH_DOMAIN", ""),
    "databaseURL": os.getenv("VITE_FIREBASE_DATABASE_URL", ""),
    "storageBucket": os.getenv("VITE_FIREBASE_STORAGE_BUCKET", "")
}

try:
    pyrebase_app = pyrebase.initialize_app(firebase_config)
    pb_auth = pyrebase_app.auth()
    logger.info("✅ Pyrebase inicializado correctamente")
except Exception as e:
    pyrebase_app = None
    pb_auth = None
    logger.warning("⚠️ Pyrebase no inicializado: %s", e)

# =========================================================
# Helpers
# =========================================================
def is_initialized() -> bool:
    """Indica si Firebase Admin fue inicializado correctamente"""
    return firebase_app is not None

def log_status() -> dict:
    """Devuelve y loguea un resumen del estado de Firebase"""
    status = {"initialized": bool(firebase_app)}

    if not firebase_app:
        logger.warning("⚠️ Firebase Admin no está inicializado")
        return status

    try:
        options = firebase_app.options
        status.update(
            {
                "app_name": firebase_app.name,
                "project_id": options.get("projectId"),
                "database_url": options.get("databaseURL"),
                "storage_bucket": options.get("storageBucket"),
                "pyrebase_initialized": pyrebase_app is not None
            }
        )
        logger.info("🔹 Estado Firebase Admin: %s", status)
    except Exception as e:
        logger.warning("⚠️ Error mostrando estado Firebase Admin: %s", e)

    return status
