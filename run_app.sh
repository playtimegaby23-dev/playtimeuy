#!/bin/bash
source venv/Scripts/activate
python app.py

echo ""
echo "Presiona Enter para salir..."
read -r
deactivate
