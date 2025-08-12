# Este archivo solo sirve para inicializar el blueprint
from flask import Blueprint

main = Blueprint('main', __name__)

from app.main import routes
