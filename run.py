import os
import logging
from app import create_app

# =========================================================
# Configuración de Logging
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# =========================================================
# Crear la instancia de Flask (Factory Pattern)
# =========================================================
app = create_app()

# =========================================================
# Ejecutar solo si es script principal
# =========================================================
if __name__ == "__main__":
    # -------------------------------
    # Configuración de entorno
    # -------------------------------
    env = os.getenv("FLASK_ENV", "production").strip().lower()

    debug_env = os.getenv("FLASK_DEBUG", "false").strip().lower()
    debug_mode = debug_env in {"1", "true", "yes"} and env != "production"

    # -------------------------------
    # Configuración de puerto
    # -------------------------------
    port_env = os.getenv("PORT", "5000").strip()
    try:
        port = int(port_env)
        if not (1 <= port <= 65535):
            raise ValueError(f"Puerto fuera de rango: {port}")
    except ValueError:
        logging.warning(f"⚠️  Variable PORT inválida ('{port_env}'), usando 5000 por defecto")
        port = 5000

    # -------------------------------
    # Configuración de host
    # -------------------------------
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0").strip() or "0.0.0.0"

    # -------------------------------
    # Mensaje inicial
    # -------------------------------
    logging.info("=" * 60)
    logging.info("🚀 Iniciando aplicación Flask")
    logging.info(f"🔹 Entorno: {env}")
    logging.info(f"🔹 Host: http://{host}:{port}")
    logging.info(f"🔹 Debug: {debug_mode}")
    logging.info("=" * 60)

    # -------------------------------
    # Ejecutar servidor Flask
    # -------------------------------
    try:
        app.run(debug=debug_mode, host=host, port=port)
    except Exception as e:
        logging.error("❌ Error iniciando el servidor", exc_info=e)
        raise
