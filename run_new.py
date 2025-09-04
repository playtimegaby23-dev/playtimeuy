# run_new.py - PlayTimeUY Ultra Profesional v3.2
from __future__ import annotations
import os
import sys
import signal
import logging
import logging.config
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import session
from werkzeug.middleware.proxy_fix import ProxyFix

# ============================================================
# PATHS Y CARGA DE ENV
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

# Selección dinámica de archivo .env
env = os.getenv("FLASK_ENV", "development").lower()
DOTENV_PATH = BASE_DIR / f".env.{env}" if env in ("development", "production") else BASE_DIR / ".env"

if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH, override=True)
    print(f"[ENV] ✅ Cargado {DOTENV_PATH}")
else:
    print("[ENV] ⚠️ No se encontró archivo .env, usando variables del sistema")

# ============================================================
# FUNCIONES DE ENV
# ============================================================
def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    return str(val).strip().lower() in {"1", "true", "yes", "on"} if val else default

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name) or default)
    except Exception:
        print(f"[ENV] ⚠️ Variable {name} inválida, usando {default}")
        return default

def _env_str(name: str, default: str | None = None) -> str:
    val = os.getenv(name)
    return (val.strip() if val else default) or default

# ============================================================
# LOGGING AVANZADO
# ============================================================
LOG_LEVEL = _env_str("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = _env_bool("LOG_TO_FILE", True)
LOG_JSON = _env_bool("LOG_JSON", False)
LOG_FILE = Path(_env_str("LOG_FILE", BASE_DIR / "playtimeuy.log"))
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

formatter = {"format": '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'} if LOG_JSON else {"format": LOG_FORMAT}

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": formatter,
        "colored": {
            "format": "\033[1;32m%(asctime)s\033[0m [\033[1;34m%(levelname)s\033[0m] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "colored",
            "stream": sys.stdout,
        },
    },
    "root": {"level": LOG_LEVEL, "handlers": ["console"]},
}

if LOG_TO_FILE:
    logging_config["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "level": LOG_LEVEL,
        "formatter": "default",
        "filename": str(LOG_FILE),
        "maxBytes": 10 * 1024 * 1024,
        "backupCount": 5,
        "encoding": "utf-8",
    }
    logging_config["root"]["handlers"].append("file")

logging.config.dictConfig(logging_config)
logger = logging.getLogger("PlayTimeUY")

# ============================================================
# CREACIÓN DE LA APP
# ============================================================
try:
    from app import create_app
    app = create_app()
    logger.info("✅ App Flask creada correctamente")
except Exception:
    logger.exception("❌ Error al crear la app Flask")
    sys.exit(1)

# ============================================================
# SEGURIDAD AVANZADA
# ============================================================
try:
    from flask_wtf import CSRFProtect
    from flask_talisman import Talisman

    CSRFProtect(app)
    csp = {
        "default-src": "'self'",
        "script-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
    }
    Talisman(
        app,
        content_security_policy=csp,
        force_https=_env_bool("FORCE_HTTPS", True),
        strict_transport_security=True,
        referrer_policy="no-referrer",
        frame_options="DENY",
        content_security_policy_nonce_in=["script-src"],
    )
    logger.info("🔒 Seguridad CSRF y Talisman activadas")
except ImportError:
    logger.warning("⚠️ Flask-WTF o Flask-Talisman no instalados, omitiendo seguridad extra")

# ============================================================
# SECRET_KEY Y VALIDACIONES DE VARIABLES CRÍTICAS
# ============================================================
REQUIRED_VARS = [
    "FLASK_SECRET_KEY",
    "FIREBASE_API_KEY",
    "FIREBASE_PROJECT_ID",
    "MERCADO_PAGO_ACCESS_TOKEN",
]
missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    logger.critical(f"❌ Variables obligatorias faltantes: {', '.join(missing)}")
    sys.exit(1)

app.config.update(
    SECRET_KEY=_env_str("FLASK_SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Strict",
)

# ============================================================
# CONFIGURACIÓN DE PROXY
# ============================================================
def _limit_proxy_val(v: int) -> int:
    return max(0, min(4, v))

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=_limit_proxy_val(_env_int("PROXY_X_FOR", 1)),
    x_proto=_limit_proxy_val(_env_int("PROXY_X_PROTO", 1)),
    x_host=_limit_proxy_val(_env_int("PROXY_X_HOST", 1)),
    x_port=_limit_proxy_val(_env_int("PROXY_X_PORT", 1)),
    x_prefix=_limit_proxy_val(_env_int("PROXY_X_PREFIX", 0)),
)

# ============================================================
# VARIABLES GLOBALES PARA JINJA
# ============================================================
app.jinja_env.globals.update(
    now=lambda: datetime.utcnow(),
    datetime=datetime,
    current_user=lambda: session.get("user"),
    has_endpoint=lambda ep: ep in app.view_functions,
)

# ============================================================
# CONFIGURACIÓN ENTORNO
# ============================================================
ENV = env
DEBUG_MODE = True if ENV == "development" else _env_bool("FLASK_DEBUG", False)
HOST = _env_str("FLASK_RUN_HOST", "0.0.0.0")
PORT = _env_int("PORT", 5000)

logger.info("=" * 60)
logger.info("🚀 PlayTimeUY Flask App")
logger.info(f"🔹 Entorno: {ENV}")
logger.info(f"🔹 Host: http://{HOST}:{PORT}")
logger.info(f"🔹 Debug: {DEBUG_MODE}")
logger.info("=" * 60)

if ENV == "production" and DEBUG_MODE:
    logger.warning("⚠️ Debug activado en PRODUCCIÓN. ¡Desactívalo!")

# ============================================================
# HANDLER GLOBAL DE ERRORES
# ============================================================
@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("❌ Error no controlado: %s", e)
    return "Ocurrió un error interno", 500

# ============================================================
# FUNCIÓN DE ARRANQUE ULTRA PROFESIONAL
# ============================================================
def run_server(host: str | None = None, port: int | None = None, debug: bool | None = None) -> None:
    h = host or HOST
    p = port or PORT
    d = DEBUG_MODE if debug is None else bool(debug)

    def _shutdown(signum, frame):
        logger.info("⏹️ Servidor detenido por señal del sistema (%s)", signum)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    if ENV == "production":
        try:
            from waitress import serve
            logger.info("🍰 Iniciando con Waitress (producción)")
            serve(app, host=h, port=p)
        except ImportError:
            logger.warning("⚠️ Waitress no instalado, usando Flask dev server")
            app.run(host=h, port=p, debug=d, threaded=True, use_reloader=False)
    else:
        logger.info("🛠️ Iniciando Flask Dev Server")
        app.run(host=h, port=p, debug=d, threaded=True, use_reloader=True)

# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================
if __name__ == "__main__":
    run_server()
