# test_app.py
import os
import json
import requests
from app.config.firebase import firestore_db, firebase_auth, firebase_storage, is_initialized

print("=== CHEQUEO INICIAL DE APP ===")

# ---------------- Firebase Admin ----------------
print("\n1️⃣ Firebase Admin:")
if is_initialized():
    print("✅ Firebase Admin inicializado")
else:
    print("❌ Firebase Admin NO inicializado")

# ---------------- Firestore ----------------
print("\n2️⃣ Firestore:")
try:
    test_doc_ref = firestore_db.collection("test").document("ping")
    test_doc_ref.set({"ping": "pong"})
    doc = test_doc_ref.get()
    if doc.exists and doc.to_dict().get("ping") == "pong":
        print("✅ Firestore OK")
    else:
        print("❌ Firestore NO OK")
except Exception as e:
    print(f"❌ Firestore ERROR: {e}")

# ---------------- Storage ----------------
print("\n3️⃣ Firebase Storage:")
try:
    blob = firebase_storage.blob("test/test.txt")
    blob.upload_from_string("ping pong")
    url = blob.public_url
    if url:
        print(f"✅ Storage OK, URL: {url}")
    else:
        print("❌ Storage NO OK")
except Exception as e:
    print(f"❌ Storage ERROR: {e}")

# ---------------- Auth ----------------
print("\n4️⃣ Firebase Auth (registro + login REST):")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
if not FIREBASE_WEB_API_KEY:
    print("⚠️ FIREBASE_WEB_API_KEY no configurada, saltando login REST")
else:
    email = "testuser@app.com"
    password = "123456"
    # Crear usuario temporal
    try:
        user = firebase_auth.create_user(email=email, password=password, display_name="Test User")
        print(f"✅ Usuario creado: {user.uid}")
    except Exception as e:
        print(f"⚠️ Usuario ya existe o error: {e}")

    # Login REST
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload)
    if resp.status_code == 200 and resp.json().get("idToken"):
        print("✅ Login REST OK")
    else:
        print(f"❌ Login REST ERROR: {resp.json()}")

# ---------------- Mercado Pago ----------------
print("\n5️⃣ Mercado Pago (preferencia de prueba):")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
if not MP_ACCESS_TOKEN:
    print("⚠️ MP_ACCESS_TOKEN no configurado, saltando test MP")
else:
    import mercadopago
    try:
        mp = mercadopago.SDK(MP_ACCESS_TOKEN)
        pref_data = {
            "items": [{"title": "Test Product", "quantity": 1, "unit_price": 10.0}],
            "payer": {"email": "testpayer@app.com"},
            "back_urls": {"success": "https://example.com/success", "failure": "https://example.com/fail"},
            "auto_return": "approved"
        }
        pref = mp.preference().create(pref_data)
        if pref.get("response", {}).get("id"):
            print(f"✅ Mercado Pago OK, preference_id: {pref['response']['id']}")
        else:
            print(f"❌ Mercado Pago NO OK: {pref}")
    except Exception as e:
        print(f"❌ Mercado Pago ERROR: {e}")

print("\n✅ CHEQUEO COMPLETO FINALIZADO")
