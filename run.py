import os
from app import create_app

# -------------------------------
# Crear la instancia de Flask
# -------------------------------
app = create_app()

# -------------------------------
# Ejecutar solo si es script principal
# -------------------------------
if __name__ == "__main__":
    # -------------------------------
    # Configuración de debug
    # -------------------------------
    debug_env = os.getenv("FLASK_DEBUG", "true").strip().lower()
    debug_mode = debug_env in {"1", "true", "yes"}

    # -------------------------------
    # Configuración de puerto
    # -------------------------------
    port_env = os.getenv("PORT", "5000").strip()
    try:
        port = int(port_env)
        if not (1 <= port <= 65535):
            raise ValueError(f"Puerto fuera de rango: {port}")
    except ValueError:
        print(f"⚠️  Variable PORT inválida ('{port_env}'), usando 5000 por defecto")
        port = 5000

    # -------------------------------
    # Configuración de host
    # -------------------------------
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1").strip() or "127.0.0.1"

    # -------------------------------
    # Mensaje inicial
    # -------------------------------
    print("=" * 50)
    print(f"🚀 Corriendo Flask App")
    print(f"🔹 Host: http://{host}:{port}")
    print(f"🔹 Debug: {debug_mode}")
    print("=" * 50)

    # -------------------------------
    # Ejecutar servidor Flask
    # -------------------------------
    try:
        app.run(debug=debug_mode, host=host, port=port)
    except Exception as e:
        print("❌ Error iniciando el servidor:", e)
