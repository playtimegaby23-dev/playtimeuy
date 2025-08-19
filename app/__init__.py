# app/__init__.py

import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    """Factory principal para crear e inicializar la aplicación Flask."""

    # === Configuración de rutas para templates y estáticos ===
    templates_path = (
        BASE_DIR / "templates"
        if (BASE_DIR / "templates").exists()
        else BASE_DIR / "app" / "templates"
    )
    static_path = (
        BASE_DIR / "static"
        if (BASE_DIR / "static").exists()
        else BASE_DIR / "app" / "static"
    )

    # Crear carpetas si no existen
    templates_path.mkdir(parents=True, exist_ok=True)
    static_path.mkdir(parents=True, exist_ok=True)

    # Crear la aplicación Flask
    app = Flask(
        __name__,
        static_folder=str(static_path),
        template_folder=str(templates_path),
    )

    # Clave secreta desde .env (fallback en dev)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-this")

    # === Context processors: funciones disponibles en todos los templates ===
    @app.context_processor
    def utility_processor():
        from flask import current_app
        return {
            "has_endpoint": lambda endpoint: endpoint in current_app.view_functions
        }

    # === Registro de blueprints ===
    try:
        from app.main.routes import main
        app.register_blueprint(main)
    except ImportError as e:
        raise RuntimeError(
            "❌ Error al importar o registrar el blueprint principal 'main'"
        ) from e

    return app
