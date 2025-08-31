//--------------------------------------------------------
// Inicialización de Firebase (Cliente / Frontend)
// ✅ Configurado con los datos exactos de PlayTimeUY
//--------------------------------------------------------

import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";
import { getStorage } from "firebase/storage";

// =========================================================
// Configuración Firebase de PlayTimeUY
// (Ideal mover a .env en producción)
// =========================================================
const firebaseConfig = {
  apiKey: "AIzaSyDbS7kMOMgx5lCL8qWJj9AHkXr-oQJgy20",
  authDomain: "playtimeuy.firebaseapp.com",
  databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com",
  projectId: "playtimeuy",
  storageBucket: "playtimeuy.appspot.com",
  messagingSenderId: "709385694606",
  appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df",
  measurementId: "G-XXXXXXXXXX", // opcional
};

// =========================================================
// Inicializar Firebase solo una vez
// =========================================================
const firebaseApp = !getApps().length
  ? initializeApp(firebaseConfig)
  : getApps()[0];

if (import.meta.env?.MODE === "development" || process.env.NODE_ENV === "development") {
  console.log(
    !getApps().length
      ? "✅ Firebase inicializado correctamente (Cliente)"
      : "♻️ Firebase ya estaba inicializado, reutilizando instancia"
  );
}

// =========================================================
// Exportar servicios principales
// =========================================================
export const firebaseAuth = getAuth(firebaseApp);
export const firestoreDb = getFirestore(firebaseApp);
export const realtimeDb = getDatabase(firebaseApp);
export const firebaseStorage = getStorage(firebaseApp);

// Export default de la app
export default firebaseApp;

// También exporto la config (útil para Analytics u otros usos)
export { firebaseConfig };

// =========================================================
// Función de debug opcional (solo dev)
// =========================================================
export function logFirebaseStatus() {
  if (import.meta.env?.MODE !== "development" && process.env.NODE_ENV !== "development") return;

  console.table({
    "Project ID": firebaseConfig.projectId,
    "Database URL": firebaseConfig.databaseURL,
    "Storage Bucket": firebaseConfig.storageBucket,
    "Auth Domain": firebaseConfig.authDomain,
    "App ID": firebaseConfig.appId,
    "Measurement ID": firebaseConfig.measurementId,
  });
}
