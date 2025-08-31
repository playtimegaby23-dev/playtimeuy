// functions/src/config/firebase.js
/**
 * Configuración centralizada de Firebase Admin SDK para el backend (Cloud Functions).
 * Usamos firebase-admin con permisos completos.
 */

import admin from "firebase-admin";

// ✅ Inicializamos la app de admin una sola vez
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com",
    storageBucket: "playtimeuy.appspot.com",
  });
}

// ✅ Exportamos los servicios principales
export const auth = admin.auth();
export const db = admin.firestore();
export const rtdb = admin.database();
export const storage = admin.storage();
export const app = admin.app();

/**
 * Helper para logging de estado de Firebase Admin
 * Ideal para debugging en entornos locales o pruebas.
 */
export const logFirebaseAdminStatus = () => {
  const options = admin.app().options;
  console.log("✅ Firebase Admin inicializado correctamente:", {
    projectId: options.projectId || "No definido",
    databaseURL: options.databaseURL || "No definido",
    storageBucket: options.storageBucket || "No definido",
  });
};
