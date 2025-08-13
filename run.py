import os
from app import create_app

# Crear la instancia de Flask
app = create_app()

# Solo se ejecuta si corremos python run.py directamente
if __name__ == "__main__":
    # Modo debug según variable de entorno FLASK_DEBUG (default True)
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # Puerto según variable de entorno PORT (default 5000)
    port_str = os.getenv("PORT", "5000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"Variable PORT inválida ('{port_str}'), usando 5000 por defecto")
        port = 5000

    # Host según variable de entorno FLASK_RUN_HOST (default 127.0.0.1)
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")

    print(f"Corriendo localmente en http://{host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, host=host, port=port)
