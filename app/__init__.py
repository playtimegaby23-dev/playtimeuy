# app/__init__.py
"""
Inicialización de la aplicación Flask PlayTimeUY.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from app.main.main_routes import main_bp
import logging

def create_app(config: dict = None) -> Flask:
    # Crear app Flask
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # --- Configuración ---
    app.config["SECRET_KEY"] = config.get("SECRET_KEY") if config else "super-secret-key"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["DEBUG"] = config.get("DEBUG") if config else True

    # --- Seguridad ---
    CSRFProtect(app)
    Talisman(app, content_security_policy=None)  # Puedes personalizar CSP si lo deseas

    # --- Registro de Blueprints ---
    app.register_blueprint(main_bp)

    # --- Logging ---
    logging.basicConfig(level=logging.INFO)
    app.logger.info("🚀 PlayTimeUY Flask App inicializada")

    # --- Manejo de errores ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Error interno: {e}")
        return render_template("errors/500.html", error=str(e)), 500

    # --- Hooks opcionales (antes/después de cada request) ---
    @app.before_request
    def before_request():
        # Aquí puedes agregar lógica antes de cada request
        pass

    @app.after_request
    def after_request(response):
        # Aquí puedes agregar headers, logging o métricas
        return response

    return app
