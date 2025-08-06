import os
from app import create_app

# Crear la app Flask usando la configuración de entorno
app = create_app()

# Ejecutar solo si este archivo es el punto de entrada
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Railway siempre maneja DEBUG=False por defecto para producción
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)
