// auth.js (Firebase v9+ modular)
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";

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
// Función para mapear errores Firebase → español
// ==============================
function getFirebaseErrorMessage(error) {
    const errorMessages = {
        "auth/email-already-in-use": "Este correo ya está registrado.",
        "auth/invalid-email": "El correo ingresado no es válido.",
        "auth/operation-not-allowed": "El inicio de sesión con este método está deshabilitado.",
        "auth/weak-password": "La contraseña es demasiado débil. Usa al menos 6 caracteres.",
        "auth/missing-password": "Debes ingresar una contraseña.",
        "auth/user-disabled": "Esta cuenta ha sido deshabilitada.",
        "auth/user-not-found": "No existe un usuario con este correo.",
        "auth/wrong-password": "La contraseña ingresada es incorrecta.",

        // Errores OAuth / Google
        "auth/popup-closed-by-user": "Cerraste la ventana de inicio de sesión antes de completar.",
        "auth/cancelled-popup-request": "Ya hay una ventana emergente abierta. Cierra la otra para continuar.",
        "auth/popup-blocked": "El navegador bloqueó la ventana de inicio de sesión. Habilítala para continuar.",
        "auth/account-exists-with-different-credential": "Ya existe una cuenta con otro método de inicio de sesión.",
        "auth/credential-already-in-use": "Las credenciales ya están en uso por otra cuenta.",
        "auth/invalid-credential": "Las credenciales no son válidas o han caducado.",

        // Red / conexión
        "auth/network-request-failed": "Error de conexión. Verifica tu internet.",
        "auth/timeout": "La solicitud tardó demasiado. Intenta nuevamente.",

        // Multi-factor
        "auth/multi-factor-auth-required": "Se requiere verificación adicional (MFA)."
    };

    return errorMessages[error.code] || error.message || "Ha ocurrido un error inesperado. Intenta nuevamente.";
}

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

            // 🔹 Validar correo (si es Google siempre viene verificado)
            if (user.emailVerified || user.providerData[0].providerId === "google.com") {
                const idToken = await user.getIdToken();

                // Enviar al backend
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
                        title: "Error en el servidor",
                        text: "Inicio de sesión válido, pero el servidor no respondió correctamente.",
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
                signOut(auth);
            }

        } catch (error) {
            console.error("Error en login con Google:", error);
            Swal.fire({
                icon: "error",
                title: "Error al iniciar sesión con Google",
                text: getFirebaseErrorMessage(error),
                confirmButtonColor: "#ef4444"
            });
        }
    });
});
