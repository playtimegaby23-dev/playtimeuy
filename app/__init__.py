import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# =========================================================
# FACTORY PRINCIPAL
# =========================================================
def create_app(config_name: str = None) -> Flask:
    """
    Crea e inicializa la aplicación Flask con configuración,
    blueprints, Firebase y manejo global de errores.
    """
    # ----------------------------- Paths -----------------------------
    base_dir = Path(__file__).resolve().parent
    root_dir = base_dir.parent
    templates_path = base_dir / "templates"
    static_path = base_dir / "static"
    logs_path = root_dir / "logs"
    for path in [templates_path, static_path, logs_path]:
        path.mkdir(parents=True, exist_ok=True)

    # ----------------------------- Carga de .env -----------------------------
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    env_file = root_dir / f".env.{config_name}"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(root_dir / ".env", override=True)

    # ----------------------------- Inicialización Flask -----------------------------
    app = Flask(__name__, template_folder=str(templates_path), static_folder=str(static_path))
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
    app.debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.config.update(
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true",
        SESSION_COOKIE_HTTPONLY=os.getenv("SESSION_COOKIE_HTTPONLY", "True").lower() == "true",
        SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16 MB
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ----------------------------- Logging -----------------------------
    log_file = logs_path / f"{config_name}.log"
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger = logging.getLogger("PlayTimeUY")
    logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    logger.info("🔑 Clave secreta cargada y logging inicializado")

    # ----------------------------- CORS -----------------------------
    cors_origins = os.getenv("CORS_ORIGINS", "")
    cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, supports_credentials=True, origins=cors_origins or "*")

    # ----------------------------- Inicialización Firebase -----------------------------
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        database_url = os.getenv("FIREBASE_DATABASE_URL")
        if service_account and database_url:
            if not os.path.exists(service_account):
                raise RuntimeError(f"Archivo de credenciales Firebase no encontrado: {service_account}")
            cred = credentials.Certificate(service_account)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {"databaseURL": database_url})
            app.firestore_db = firestore.client()
            logger.info("✅ Firebase Admin inicializado correctamente")
        else:
            logger.warning("⚠️ Firebase Admin no inicializado: variables de entorno faltantes")
    except Exception as e:
        logger.warning(f"⚠️ Firebase Admin no inicializado ({e})")

    # ----------------------------- Blueprints -----------------------------
    try:
        from app.main.main_routes import main_bp
        from app.main.user_routes import user_bp
        from app.auth_routes import auth_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(user_bp, url_prefix="/users")
        app.register_blueprint(auth_bp, url_prefix="/auth")
        logger.info("✅ Blueprints registrados correctamente")
    except Exception as e:
        logger.exception("❌ Error registrando blueprints")
        raise RuntimeError("No se pudo registrar los blueprints") from e

    # ----------------------------- Context processor global -----------------------------
    @app.context_processor
    def utility_processor():
        from datetime import datetime, timezone
        return {
            "current_year": lambda: datetime.now().year,
            "utc_now": lambda: datetime.now(timezone.utc),
            "app_name": "PlayTimeUY",
            "env": config_name,
        }

    # ----------------------------- Sessions -----------------------------
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # ----------------------------- Manejo global de errores -----------------------------
    def wants_json() -> bool:
        return request.accept_mimetypes.best == "application/json" or request.path.startswith("/api/")

    @app.errorhandler(404)
    def not_found(error):
        if wants_json():
            return jsonify(ok=False, error="Recurso no encontrado"), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        if wants_json():
            return jsonify(ok=False, error="Error interno del servidor"), 500
        return render_template("errors/500.html", error=error), 500

    @app.errorhandler(Exception)
    def handle_all_exceptions(error):
        if wants_json():
            return jsonify(ok=False, error=str(error)), 500
        return render_template("errors/500.html", error=error), 500

    logger.info("✅ App Flask creada correctamente")
    return app
