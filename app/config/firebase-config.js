/**
 * config.js
 * --------------------------------------------------------
 * Configuración centralizada de Firebase y Mercado Pago
 * ✅ Inicializa Firebase (SDK modular v9+)
 * ✅ Exporta servicios: Auth, Firestore, RTDB, Storage
 * ✅ Configura Mercado Pago para frontend
 * ✅ Compatible con Vite, Next.js, Node, Webpack
 * ✅ Seguro en SSR (Next.js, Remix)
 */

// =========================================================
// 1. Firebase
// =========================================================
import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getDatabase } from "firebase/database";
import { getStorage } from "firebase/storage";

// Configuración de Firebase
const firebaseConfig = {
  apiKey: "AIzaSyDbS7kMOMgx5lCL8qWJj9AHkXr-oQJgy20",
  authDomain: "playtimeuy.firebaseapp.com",
  databaseURL: "https://playtimeuy-default-rtdb.firebaseio.com",
  projectId: "playtimeuy",
  storageBucket: "playtimeuy.firebasestorage.app",
  messagingSenderId: "709385694606",
  appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df",
};

// Inicializar Firebase una sola vez
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

// Exportar servicios de Firebase
export const firebaseAuth = getAuth(app);
export const firebaseDB = getFirestore(app);
export const firebaseRTDB = getDatabase(app);
export const firebaseStorage = getStorage(app);

// =========================================================
// 2. Mercado Pago (Frontend)
// =========================================================
export const MP_CONFIG = {
  accessToken: "APP_USR-d28c8e91-bfe9-4750-9e83-62968c5ce0eb",
  publicKey: "APP_USR-8983986661644091-081911-db4d3357b3a9cc4c1fc9d6c0f9283991-1631824500",
  integratorId: "ooASLjqDMNHGQq55QRtkraEdPzTehQkn",
  currency: "UYU",
  basePrice: 750,
  urls: {
    success: "https://playtimeuy.com/checkout/success",
    failure: "https://playtimeuy.com/checkout/failure",
    pending: "https://playtimeuy.com/checkout/pending",
    webhook: "https://playtimeuy.com/webhooks/mercadopago",
  },
};

// =========================================================
// 3. Funciones auxiliares
// =========================================================
export function logConfig() {
  console.log("📊 [Config] Firebase:", {
    projectId: firebaseConfig.projectId,
    databaseURL: firebaseConfig.databaseURL,
    storageBucket: firebaseConfig.storageBucket,
  });
  console.log("📊 [Config] Mercado Pago:", MP_CONFIG);
}

// =========================================================
// 4. Export default
// =========================================================
export default {
  app,
  firebaseAuth,
  firebaseDB,
  firebaseRTDB,
  firebaseStorage,
  MP_CONFIG,
  logConfig,
};
