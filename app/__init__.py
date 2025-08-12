import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

def create_app():
    # Definir rutas de templates y static
    if (BASE_DIR / "templates").exists():
        templates_path = BASE_DIR / "templates"
    elif (BASE_DIR / "app" / "templates").exists():
        templates_path = BASE_DIR / "app" / "templates"
    else:
        templates_path = BASE_DIR / "templates"
        templates_path.mkdir(parents=True, exist_ok=True)

    if (BASE_DIR / "static").exists():
        static_path = BASE_DIR / "static"
    elif (BASE_DIR / "app" / "static").exists():
        static_path = BASE_DIR / "app" / "static"
    else:
        static_path = BASE_DIR / "static"
        static_path.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        static_folder=str(static_path),
        template_folder=str(templates_path)
    )

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-this")

    # Registrar blueprints
    from app.main.routes import main
    app.register_blueprint(main)

    return app
