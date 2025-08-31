"""
Local Storage de usuarios para PlayTimeUY
-----------------------------------------
✅ Guarda datos locales (edad, lugar, nacionalidad, bio, etc.)
✅ Logging profesional
✅ Manejo seguro de errores
✅ Compatible con sesión y uid de Firebase
"""

import json
from pathlib import Path
import logging

logger = logging.getLogger("PlayTimeUY.local_storage")

# ===================== RUTAS =====================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # Crear carpeta si no existe
LOCAL_DB_PATH = DATA_DIR / "local_users.json"

# ===================== FUNCIONES =====================
def save_user_local(uid: str, extra_data: dict):
    """
    Guardar datos extra de usuario en JSON local.
    - uid: ID único del usuario (Firebase)
    - extra_data: diccionario con datos extra (edad, lugar, nacionalidad, etc.)
    """
    try:
        # Cargar datos existentes
        if LOCAL_DB_PATH.exists():
            with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # Actualizar usuario
        data[uid] = extra_data

        # Guardar archivo
        with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("✅ Datos locales guardados para UID=%s", uid)

    except Exception as e:
        logger.exception("❌ Error guardando datos locales para UID=%s: %s", uid, e)


def load_user_local(uid: str) -> dict:
    """
    Cargar datos extra de usuario desde JSON local.
    - uid: ID único del usuario (Firebase)
    - Retorna diccionario vacío si no hay datos
    """
    if not LOCAL_DB_PATH.exists():
        return {}
    try:
        with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(uid, {})
    except Exception as e:
        logger.exception("❌ Error cargando datos locales para UID=%s: %s", uid, e)
        return {}
