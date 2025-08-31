// firebase-config.js
/**
 * Configuración y exportación centralizada de Firebase (modular SDK v9+).
 * - Inicializa Firebase una única vez.
 * - Exporta: auth, db (Firestore), rtdb (Realtime DB), storage.
 * - Permite override de config (initFirebase) y conexión a emuladores (useEmulators).
 *
 * Uso:
 *  import { auth, db, rtdb, storage, initFirebase, useEmulators, logStatus } from './firebase-config';
 *
 * Si querés pasar otra config (ej. en tests), llamá initFirebase({ ... }) antes de usar los servicios.
 */

import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getDatabase, connectDatabaseEmulator } from "firebase/database";
import { getStorage, connectStorageEmulator } from "firebase/storage";

// -----------------
// DEFAULT CONFIG
// -----------------
// Mantengo la configuración que compartiste como valores por defecto.
// En producción podés reemplazar llamando initFirebase({ ... }) con valores desde tu .env
const DEFAULT_FIREBASE_CONFIG = {
  apiKey: "AIzaSyDbS7kMOMgx5lCL8qWJj9AHkXr-oQJgy20",
  authDomain: "playtimeuy.firebaseapp.com",
  databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com",
  projectId: "playtimeuy",
  storageBucket: "playtimeuy.appspot.com",
  messagingSenderId: "709385694606",
  appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df",
};

// Internal state
let _app = null;
let _auth = null;
let _firestore = null;
let _rtdb = null;
let _storage = null;
let _initializedWith = null;
let _usingEmulators = false;

/**
 * initFirebase(config)
 * Inicializa Firebase si no está inicializado. Devuelve el app inicializado.
 * - config (opcional): objeto con la misma forma que DEFAULT_FIREBASE_CONFIG para sobreescribir.
 *                      Si no se pasa, usa DEFAULT_FIREBASE_CONFIG.
 *
 * Puedes llamar initFirebase() varias veces; solo inicializará la primera vez.
 */
export function initFirebase(config = {}) {
  const finalConfig = { ...DEFAULT_FIREBASE_CONFIG, ...(config || {}) };

  try {
    if (getApps().length) {
      // Si ya hay una app, la reutilizamos (útil en hot-reload)
      _app = getApp();
      _initializedWith = _initializedWith || finalConfig;
    } else {
      _app = initializeApp(finalConfig);
      _initializedWith = finalConfig;
    }

    // Inicializar servicios (lazy-safe: si ya existen, los sobrescribimos con la misma instancia)
    _auth = _auth || getAuth(_app);
    _firestore = _firestore || getFirestore(_app);
    _rtdb = _rtdb || getDatabase(_app);
    _storage = _storage || getStorage(_app);

    // Dev-time log
    if (process && process.env && process.env.NODE_ENV === "development") {
      // eslint-disable-next-line no-console
      console.info("[firebase-config] Firebase inicializado con config:", {
        projectId: finalConfig.projectId,
        authDomain: finalConfig.authDomain,
        databaseURL: finalConfig.databaseURL,
        storageBucket: finalConfig.storageBucket,
      });
    }

    return _app;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("[firebase-config] Error inicializando Firebase:", err);
    throw err;
  }
}

/**
 * useEmulators({ host, authPort, firestorePort, rtdbPort, storagePort })
 * Conecta los SDKs a los emuladores locales (solo cuando initFirebase ya fue llamado).
 *
 * Ejemplo:
 *   useEmulators({ host: 'localhost', firestorePort: 8080, rtdbPort: 9000, storagePort: 9199 })
 */
export function useEmulators({
  host = "localhost",
  firestorePort,
  rtdbPort,
  storagePort,
} = {}) {
  if (!_app || !_firestore || !_rtdb || !_storage) {
    throw new Error("Firebase no inicializado. Llamá primero initFirebase(config).");
  }

  _usingEmulators = true;

  try {
    if (firestorePort) {
      connectFirestoreEmulator(_firestore, host, firestorePort);
    }
    if (rtdbPort) {
      connectDatabaseEmulator(_rtdb, host, rtdbPort);
    }
    if (storagePort) {
      connectStorageEmulator(_storage, host, storagePort);
    }

    // eslint-disable-next-line no-console
    console.info(`[firebase-config] Emulators conectados -> host: ${host}`, {
      firestorePort,
      rtdbPort,
      storagePort,
    });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("[firebase-config] Error conectando emuladores:", err);
    throw err;
  }
}

/**
 * getFirebaseServices()
 * Devuelve un objeto con las instancias ya inicializadas: { app, auth, db, rtdb, storage }
 * Si no fueron inicializadas, intenta inicializar con DEFAULT_FIREBASE_CONFIG.
 */
export function getFirebaseServices() {
  if (!_app) {
    initFirebase();
  }
  return {
    app: _app,
    auth: _auth,
    db: _firestore,
    rtdb: _rtdb,
    storage: _storage,
    usingEmulators: _usingEmulators,
    initializedWith: _initializedWith,
  };
}

/**
 * logStatus() - imprime un resumen de estado (útil en desarrollo)
 */
export function logStatus() {
  const services = getFirebaseServices();
  // eslint-disable-next-line no-console
  console.log("Firebase status:", {
    appName: services.app?.name,
    projectId: services.initializedWith?.projectId,
    auth: !!services.auth,
    firestore: !!services.db,
    realtimeDB: !!services.rtdb,
    storage: !!services.storage,
    usingEmulators: services.usingEmulators,
  });
}

/* ----------------------------
   Inicialización automática (por defecto)
   ---------------------------- */
/**
 * Si querés evitar la inicialización automática (p. ej. en tests), llamá initFirebase(null)
 * antes de importar/usar este módulo.
 */
try {
  // Llamamos initFirebase solo si aún no está inicializada (evita errores en SSR/hot-reload)
  if (!getApps().length) {
    initFirebase(); // usa DEFAULT_FIREBASE_CONFIG
  } else {
    _app = getApp();
    _auth = getAuth(_app);
    _firestore = getFirestore(_app);
    _rtdb = getDatabase(_app);
    _storage = getStorage(_app);
  }
} catch (err) {
  // eslint-disable-next-line no-console
  console.warn("[firebase-config] Inicialización automática fallida (puede ser intencional):", err);
}

/* ----------------------------
   Exports por defecto de servicios
   ---------------------------- */
export const auth = _auth;
export const db = _firestore;
export const rtdb = _rtdb;
export const storage = _storage;

export default {
  initFirebase,
  getFirebaseServices,
  useEmulators,
  logStatus,
  auth,
  db,
  rtdb,
  storage,
};
