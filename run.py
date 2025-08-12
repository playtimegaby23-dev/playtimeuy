from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    port_str = os.getenv("PORT", "5000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"Variable PORT inválida ('{port_str}'), usando 5000 por defecto")
        port = 5000
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    app.run(debug=debug_mode, host=host, port=port)
