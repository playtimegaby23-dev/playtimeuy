from flask import Flask
from .routes import main

def create_app():
    app = Flask(__name__)
    app.secret_key = 'tu_clave_secreta'  # Necesaria para flash messages

    app.register_blueprint(main)

    return app
