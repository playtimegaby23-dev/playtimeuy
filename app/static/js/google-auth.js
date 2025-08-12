import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.12.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "{{ FIREBASE_API_KEY }}",
  authDomain: "{{ FIREBASE_AUTH_DOMAIN }}",
  projectId: "{{ FIREBASE_PROJECT_ID }}",
  storageBucket: "{{ FIREBASE_STORAGE_BUCKET }}",
  messagingSenderId: "{{ FIREBASE_MESSAGING_SENDER_ID }}",
  appId: "{{ FIREBASE_APP_ID }}"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

document.getElementById("google-login-btn").addEventListener("click", () => {
  signInWithPopup(auth, provider)
    .then(result => result.user.getIdToken())
    .then(idToken => {
      return fetch("/login/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken })
      });
    })
    .then(response => {
      if (response.redirected) {
        window.location.href = response.url;
      } else {
        alert("Error en inicio de sesión con Google");
      }
    })
    .catch(error => {
      console.error("Google Sign-In error:", error);
      alert("Error al iniciar sesión con Google.");
    });
});
