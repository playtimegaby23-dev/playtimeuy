// firebase-config.js
/**
 * Configuración y exportación de Firebase para toda la app.
 * Incluye: Authentication, Firestore y Realtime Database.
 */

import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";

// 🔹 Configuración de tu proyecto Firebase
const firebaseConfig = {
  apiKey: "AIzaSyDbS7kMOMgx5lCL8qWJj9AHkXr-oQJgy20",
  authDomain: "playtimeuy.firebaseapp.com",
  databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com", // Realtime Database
  projectId: "playtimeuy",
  storageBucket: "playtimeuy.appspot.com",
  messagingSenderId: "709385694606",
  appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df"
};

// 🔹 Inicializa Firebase solo si aún no existe
const app = !getApps().length ? initializeApp(firebaseConfig) : getApps()[0];

// 🔹 Exportar servicios de Firebase
export const auth = getAuth(app);        // Autenticación de usuarios
export const db = getFirestore(app);     // Firestore (NoSQL)
export const rtdb = getDatabase(app);    // Realtime Database

// 🔹 Función de ayuda opcional para depuración
export const logFirebaseStatus = () => {
  console.log("✅ Firebase inicializado:", {
    appName: app.name,
    auth: !!auth,
    firestore: !!db,
    realtimeDB: !!rtdb
  });
};
