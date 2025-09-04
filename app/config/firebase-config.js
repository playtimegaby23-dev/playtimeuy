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

// Configuración de Firebase (PlayTimeUY 2025)
const firebaseConfig = {
  apiKey: "AIzaSyADuExp0K-vavTq5Yefk9Qo_yCdr4DC8aM",
  authDomain: "playtime2025.firebaseapp.com",
  databaseURL: "https://playtime2025-default-rtdb.firebaseio.com",
  projectId: "playtime2025",
  storageBucket: "playtime2025.firebasestorage.app",
  messagingSenderId: "8394953810",
  appId: "1:8394953810:web:7ac9fdcad79b4ebbd33b8b",
  measurementId: "G-XXXXXXXXXX", // opcional si usás Analytics
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
// ⚠️ Recomendado: mover accessToken/publicKey a variables de entorno
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
  if (import.meta.env?.MODE !== "development" && process.env.NODE_ENV !== "development") return;

  console.log("📊 [Config] Firebase:", {
    projectId: firebaseConfig.projectId,
    databaseURL: firebaseConfig.databaseURL,
    storageBucket: firebaseConfig.storageBucket,
    authDomain: firebaseConfig.authDomain,
    appId: firebaseConfig.appId,
  });

  console.log("📊 [Config] Mercado Pago:", {
    currency: MP_CONFIG.currency,
    basePrice: MP_CONFIG.basePrice,
    urls: MP_CONFIG.urls,
    integratorId: MP_CONFIG.integratorId,
  });
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
