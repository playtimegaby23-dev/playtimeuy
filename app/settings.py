from __future__ import annotations

import os
import json
import logging
import secrets
from datetime import timedelta
from typing import Optional, Any, Iterable, Dict, Union

# ============================
# Helpers internos
# ============================
def _bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")

def _int(val: Optional[str], default: int = 0) -> int:
    try:
        return int(val) if val is not None and str(val).strip() != "" else default
    except (TypeError, ValueError):
        return default

def _json(val: Optional[str], default: Any = None) -> Any:
    if not val:
        return default
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        return default

def env_first(names: Iterable[str], default: Optional[str] = None) -> Optional[str]:
    for name in names:
        v = os.getenv(name)
        if v is not None and str(v).strip() != "":
            return v
    return default

def _read_service_account() -> Optional[Union[dict, str]]:
    """
    Lee credenciales de Firebase:
      - Primero intenta leer JSON inline desde FIREBASE_SERVICE_ACCOUNT_JSON
      - Luego intenta leer ruta desde FIREBASE_SERVICE_ACCOUNT
      - Si no hay nada, devuelve None (no se lanza excepción aquí).
    Retorna diccionario (parsed JSON) o ruta absoluta (string).
    """
    json_inline = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if json_inline:
        try:
            parsed = json.loads(json_inline)
            return parsed
        except json.JSONDecodeError as e:
            raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_JSON inválido: {e}")

    path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if path:
        # Acepta rutas relativas y absolutas
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return os.path.abspath(path)
        raise FileNotFoundError(f"Archivo de service account no encontrado en: {path}")

    return None

# ============================
# Settings principal
# ============================
class Settings:
    # -----------------------
    # Entorno & Flask
    # -----------------------
    ENV: str = os.getenv("FLASK_ENV", "development").lower()
    DEBUG: bool = _bool(os.getenv("FLASK_DEBUG"), ENV == "development")
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY") or secrets.token_urlsafe(48)
    PORT: int = _int(os.getenv("PORT"), 5000)

    # -----------------------
    # Cookies / sesiones / seguridad
    # -----------------------
    SESSION_COOKIE_SECURE: bool = _bool(os.getenv("SESSION_COOKIE_SECURE"), ENV == "production")
    SESSION_COOKIE_SAMESITE: str = os.getenv("SESSION_COOKIE_SAMESITE", "Strict" if ENV == "production" else "Lax")
    SESSION_COOKIE_HTTPONLY: bool = _bool(os.getenv("SESSION_COOKIE_HTTPONLY"), True)
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=_int(os.getenv("SESSION_LIFETIME_DAYS"), 7))
    CSRF_ENABLED: bool = _bool(os.getenv("CSRF_ENABLED"), True)
    SECURE_PROXY_SSL_HEADER = ("X-Forwarded-Proto", "https")

    # -----------------------
    # CORS
    # -----------------------
    _cors_raw = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS = [o.strip() for o in _cors_raw.split(",") if o.strip()]
    CORS_SUPPORTS_CREDENTIALS: bool = _bool(os.getenv("CORS_SUPPORTS_CREDENTIALS"), True)

    # -----------------------
    # Logging
    # -----------------------
    LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "DEBUG" if ENV == "development" else "INFO").upper(), logging.INFO)
    LOG_FORMAT = os.getenv("LOG_FORMAT", "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    LOG_DATEFMT = os.getenv("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S")

    # -----------------------
    # Firebase Admin (backend)
    # -----------------------
    # Puede ser dict (JSON inline) o ruta string
    FIREBASE_SERVICE_ACCOUNT: Optional[Union[dict, str]] = _read_service_account()
    FIREBASE_DATABASE_URL: Optional[str] = os.getenv("FIREBASE_DATABASE_URL")
    FIREBASE_STORAGE_BUCKET: Optional[str] = os.getenv("FIREBASE_STORAGE_BUCKET")

    # -----------------------
    # Firebase cliente / REST (frontend)
    # -----------------------
    FIREBASE_API_KEY: Optional[str] = env_first(["FIREBASE_API_KEY", "FIREBASE_WEB_API_KEY"])
    FIREBASE_AUTH_DOMAIN: Optional[str] = os.getenv("FIREBASE_AUTH_DOMAIN")
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID: Optional[str] = os.getenv("FIREBASE_APP_ID")
    FIREBASE_MEASUREMENT_ID: Optional[str] = os.getenv("FIREBASE_MEASUREMENT_ID")
    VITE_FIREBASE_API_KEY = os.getenv("VITE_FIREBASE_API_KEY") or FIREBASE_API_KEY
    VITE_FIREBASE_AUTH_DOMAIN = os.getenv("VITE_FIREBASE_AUTH_DOMAIN") or FIREBASE_AUTH_DOMAIN
    VITE_FIREBASE_PROJECT_ID = os.getenv("VITE_FIREBASE_PROJECT_ID") or FIREBASE_PROJECT_ID
    VITE_FIREBASE_STORAGE_BUCKET = os.getenv("VITE_FIREBASE_STORAGE_BUCKET") or FIREBASE_STORAGE_BUCKET
    VITE_FIREBASE_MESSAGING_SENDER_ID = os.getenv("VITE_FIREBASE_MESSAGING_SENDER_ID") or FIREBASE_MESSAGING_SENDER_ID
    VITE_FIREBASE_APP_ID = os.getenv("VITE_FIREBASE_APP_ID") or FIREBASE_APP_ID
    VITE_FIREBASE_MEASUREMENT_ID = os.getenv("VITE_FIREBASE_MEASUREMENT_ID") or FIREBASE_MEASUREMENT_ID
    VITE_FIREBASE_DATABASE_URL = os.getenv("VITE_FIREBASE_DATABASE_URL") or FIREBASE_DATABASE_URL

    # -----------------------
    # Mercado Pago
    # -----------------------
    MP_ENV: str = os.getenv("MP_ENV", "sandbox" if ENV == "development" else "production")
    MERCADO_PAGO_ACCESS_TOKEN: str = env_first(["MERCADO_PAGO_ACCESS_TOKEN", "MP_ACCESS_TOKEN"], "")
    MERCADO_PAGO_PUBLIC_KEY: str = env_first(["MERCADO_PAGO_PUBLIC_KEY", "MP_PUBLIC_KEY"], "")
    MERCADO_PAGO_CURRENCY: str = env_first(["MERCADO_PAGO_CURRENCY", "MP_CURRENCY"], "UYU")
    MERCADO_PAGO_BASE_PRICE: int = _int(env_first(["MERCADO_PAGO_BASE_PRICE", "MP_BASE_PRICE"], "0"), 0)

    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000" if ENV == "development" else "https://playtimeuy.com")
    MERCADO_PAGO_SUCCESS_URL: str = env_first(["MERCADO_PAGO_SUCCESS_URL", "MP_SUCCESS_URL"], f"{APP_BASE_URL}/checkout/success")
    MERCADO_PAGO_FAILURE_URL: str = env_first(["MERCADO_PAGO_FAILURE_URL", "MP_FAILURE_URL"], f"{APP_BASE_URL}/checkout/failure")
    MERCADO_PAGO_PENDING_URL: str = env_first(["MERCADO_PAGO_PENDING_URL", "MP_PENDING_URL"], f"{APP_BASE_URL}/checkout/pending")
    MERCADO_PAGO_WEBHOOK_URL: str = env_first(["MERCADO_PAGO_WEBHOOK_URL", "MP_WEBHOOK_URL"], f"{APP_BASE_URL}/webhooks/mercadopago")
    MERCADO_PAGO_EXTERNAL_REFERENCE_PREFIX: str = env_first(
        ["MERCADO_PAGO_EXTERNAL_REFERENCE_PREFIX", "MP_EXTERNAL_REFERENCE_PREFIX"],
        f"playtimeuy-{'dev' if ENV == 'development' else 'prod'}",
    )

    MP_WEBHOOK_SECRET: str = os.getenv("MP_WEBHOOK_SECRET", "")
    MP_ALLOWED_IPS = [ip.strip() for ip in os.getenv("MP_ALLOWED_IPS", "").split(",") if ip.strip()]

    # -----------------------
    # PWA & extras
    # -----------------------
    PWA_ENABLED: bool = _bool(os.getenv("PWA_ENABLED"), True)
    PWA_MANIFEST_PATH: str = os.getenv("PWA_MANIFEST_PATH", "static/manifest.json")
    MAX_CONTENT_LENGTH: int = _int(os.getenv("MAX_CONTENT_LENGTH_MB"), 16) * 1024 * 1024
    RATE_LIMIT_ENABLED: bool = _bool(os.getenv("RATE_LIMIT_ENABLED"), True)

    # -----------------------
    # Comportamiento al import (controlable)
    # -----------------------
    VALIDATE_ON_IMPORT: bool = _bool(os.getenv("VALIDATE_SETTINGS_ON_IMPORT"), False)

    # =======================
    # Métodos utilitarios
    # =======================
    @classmethod
    def init_logging(cls) -> None:
        """Configura logging básico y reduce ruido en producción."""
        logging.basicConfig(level=cls.LOG_LEVEL, format=cls.LOG_FORMAT, datefmt=cls.LOG_DATEFMT)
        root = logging.getLogger()
        # Evitar handlers duplicados
        if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
            root.addHandler(logging.StreamHandler())
        # Ajuste de werkzeug
        logging.getLogger("werkzeug").setLevel(logging.WARNING if cls.ENV == "production" else logging.INFO)

    @classmethod
    def validate(cls) -> None:
        """
        Valida variables críticas. Lanza RuntimeError con mensaje claro si faltan.
        No se ejecuta automáticamente a menos que VALIDATE_ON_IMPORT=True.
        """
        missing = []

        # Validaciones mínimas para que funciones backend principales trabajen
        if not cls.FIREBASE_API_KEY and not cls.FIREBASE_SERVICE_ACCOUNT:
            missing.append("FIREBASE_API_KEY o FIREBASE_SERVICE_ACCOUNT (credenciales Firebase)")

        if not cls.MERCADO_PAGO_ACCESS_TOKEN:
            missing.append("MERCADO_PAGO_ACCESS_TOKEN (MP_ACCESS_TOKEN)")

        if cls.ENV == "production":
            if not str(cls.APP_BASE_URL).startswith("https://"):
                missing.append("APP_BASE_URL (debe usar https en producción)")
            if not str(cls.MERCADO_PAGO_WEBHOOK_URL).startswith("https://"):
                missing.append("MERCADO_PAGO_WEBHOOK_URL (https recomendado)")

        if missing:
            raise RuntimeError("Variables obligatorias faltantes: " + ", ".join(missing))

    @classmethod
    def as_dict(cls, include_secrets: bool = False) -> Dict[str, Any]:
        """Resumen de configuración. Por defecto oculta valores sensibles."""
        out = {
            "env": cls.ENV,
            "debug": cls.DEBUG,
            "port": cls.PORT,
            "cors_origins": cls.CORS_ORIGINS,
            "firebase_project": cls.FIREBASE_PROJECT_ID,
            "firebase_db_url": bool(cls.FIREBASE_DATABASE_URL),
            "firebase_service_account": True if cls.FIREBASE_SERVICE_ACCOUNT else False,
            "mercadopago_env": cls.MP_ENV,
            "mercadopago_currency": cls.MERCADO_PAGO_CURRENCY,
            "app_base_url": cls.APP_BASE_URL,
            "pwa_enabled": cls.PWA_ENABLED,
            "rate_limit_enabled": cls.RATE_LIMIT_ENABLED,
            "max_upload_mb": int(cls.MAX_CONTENT_LENGTH / (1024 * 1024)),
        }
        if include_secrets:
            out.update({
                "firebase_service_account_raw": cls.FIREBASE_SERVICE_ACCOUNT,
                "mercadopago_access_token": cls.MERCADO_PAGO_ACCESS_TOKEN,
                "mercadopago_public_key": cls.MERCADO_PAGO_PUBLIC_KEY,
            })
        return out

# ============================
# Inicialización por defecto
# ============================
# Configura logging al importar (ligero)
Settings.init_logging()

# Validación temprana opcional (controlá con VALIDATE_SETTINGS_ON_IMPORT=1 si la querés)
if Settings.VALIDATE_ON_IMPORT:
    try:
        Settings.validate()
    except Exception as e:
        logging.getLogger("PlayTimeUY").critical("Settings inválidos: %s", e)
        raise

# Fin de settings.py
