# app/firebase_admin_ext.py
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, db
from flask import current_app

def init_firebase_admin():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    cfg = current_app.config
    sa = cfg.get("FIREBASE_SERVICE_ACCOUNT")
    if not sa:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT no configurado en env.")
    # si proviene como dict (JSON inline) lo aceptamos
    if isinstance(sa, dict):
        cred = credentials.Certificate(sa)
    else:
        cred = credentials.Certificate(str(sa))
    app = initialize_app(cred, {
        "databaseURL": cfg.get("FIREBASE_DATABASE_URL"),
        "storageBucket": cfg.get("FIREBASE_STORAGE_BUCKET"),
    })
    return app

def get_bucket():
    init_firebase_admin()
    return storage.bucket()

def get_rtdb():
    init_firebase_admin()
    return db
