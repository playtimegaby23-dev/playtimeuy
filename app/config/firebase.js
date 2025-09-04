//--------------------------------------------------------
// Inicialización de Firebase (Cliente / Frontend)
// ✅ Configurado con los datos exactos de PlayTimeUY 2025
//--------------------------------------------------------

import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";
import { getStorage } from "firebase/storage";

// =========================================================
// Configuración Firebase de PlayTimeUY 2025
// (⚠️ Recomendado mover a variables de entorno en producción)
// =========================================================
const firebaseConfig = {
  apiKey: "AIzaSyADuExp0K-vavTq5Yefk9Qo_yCdr4DC8aM",
  authDomain: "playtime2025.firebaseapp.com",
  databaseURL: "https://playtime2025-default-rtdb.firebaseio.com",
  projectId: "playtime2025",
  storageBucket: "playtime2025.firebasestorage.app",
  messagingSenderId: "8394953810",
  appId: "1:8394953810:web:7ac9fdcad79b4ebbd33b8b",
  measurementId: "G-XXXXXXXXXX", // opcional si activás Analytics
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
// Función de debug opcional (solo en desarrollo)
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
