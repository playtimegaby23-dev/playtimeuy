import os
from app import create_app

# Crear la app Flask usando la configuración de entorno
app = create_app()

# Ejecutar solo si este archivo es el punto de entrada
if __name__ == "__main__":
    # Obtener el puerto desde variables de entorno o usar 5000 por defecto
    port = int(os.environ.get("PORT", 5000))

    # Definir si se ejecuta en modo debug (por defecto True si no se define DEBUG)
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

    # Ejecutar la app
    app.run(host="0.0.0.0", port=port, debug=debug)
