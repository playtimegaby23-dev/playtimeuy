// auth.js (Firebase v9+ modular)
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

// 🔹 Configuración de Firebase
const firebaseConfig = {
    apiKey: "AIzaSyD8cKZyxIvZ6Uq3W7y2cUJdyteZGUdtNNg",
    authDomain: "playtimeuy.firebaseapp.com",
    projectId: "playtimeuy",
    storageBucket: "playtimeuy.appspot.com",
    messagingSenderId: "709385694606",
    appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df"
};

// 🔹 Inicializar Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// ==============================
// Google Login
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    const googleBtn = document.getElementById("google-login");
    if (!googleBtn) return;

    googleBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
            const result = await signInWithPopup(auth, provider);
            const user = result.user;

            if (user.emailVerified || user.providerData[0].providerId === "google.com") {
                const idToken = await user.getIdToken(); // 🔹 Token seguro para backend

                const res = await fetch("/login/google", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ idToken })
                });

                if (res.redirected) {
                    window.location.href = res.url;
                } else {
                    Swal.fire({
                        icon: "error",
                        title: "Algo salió mal",
                        text: "Inicio de sesión exitoso pero no se pudo iniciar sesión en el servidor.",
                        confirmButtonColor: "#ef4444"
                    });
                }
            } else {
                Swal.fire({
                    icon: "warning",
                    title: "Correo no verificado",
                    text: "Tu correo debe estar verificado para continuar.",
                    confirmButtonColor: "#f59e0b"
                });
                auth.signOut();
            }
        } catch (error) {
            console.error("Error en login con Google:", error);
            Swal.fire({
                icon: "error",
                title: "Error al iniciar sesión con Google",
                text: error.message || "Intenta nuevamente.",
                confirmButtonColor: "#ef4444"
            });
        }
    });
});
