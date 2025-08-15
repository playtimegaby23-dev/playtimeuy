// firebase-config.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";

// Configuración de tu proyecto Firebase
const firebaseConfig = {
  apiKey: "AIzaSyDbS7kMOMgx5lCL8qWJj9AHkXr-oQJgy20",
  authDomain: "playtimeuy.firebaseapp.com",
  databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com", // 🔹 Realtime Database
  projectId: "playtimeuy",
  storageBucket: "playtimeuy.firebasestorage.app",
  messagingSenderId: "709385694606",
  appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df"
};

// Inicializa la app
const app = initializeApp(firebaseConfig);

// Exporta las instancias para usarlas en el resto de la app
export const auth = getAuth(app);          // Autenticación
export const db = getFirestore(app);       // Firestore
export const rtdb = getDatabase(app);      // Realtime Database
