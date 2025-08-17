import { auth, db } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "firebase/auth";
import { collection, query, where, getDocs } from "firebase/firestore";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    if (!form) {
        console.error("❌ No se encontró el formulario con id='loginForm'");
        return;
    }

    // Inputs
    const userInput = form.querySelector("input[name='user']"); // email o username
    const passInput = form.querySelector("input[name='password']");

    // 🔹 Animación de error
    function animateError(input) {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    }

    // 🔹 Validaciones
    function validateRequired(input) {
        const isValid = input.value.trim() !== "";
        if (!isValid) animateError(input);
        return isValid;
    }

    function validatePassword(input) {
        const value = input.value.trim();
        const isValid = value.length >= 6;
        if (!isValid) animateError(input);
        return isValid;
    }

    // 🔹 Validación en tiempo real
    userInput.addEventListener("input", () => validateRequired(userInput));
    passInput.addEventListener("input", () => validatePassword(passInput));

    // 🔹 Obtener email si ingresan username
    async function resolveEmailFromUsername(username) {
        try {
            const q = query(collection(db, "usuarios"), where("username", "==", username.trim()));
            const snapshot = await getDocs(q);
            if (!snapshot.empty) {
                return snapshot.docs[0].data().email; // Devuelve email asociado al username
            }
            return null;
        } catch (err) {
            console.error("❌ Error buscando username:", err);
            return null;
        }
    }

    // 🔹 Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateRequired(userInput) || !validatePassword(passInput)) {
            Swal.fire("Error", "Por favor completa todos los campos correctamente.", "error");
            return;
        }

        try {
            Swal.fire({
                title: "Iniciando sesión...",
                text: "Por favor espera",
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading(),
                background: "#1f1f2e",
                color: "#fff"
            });

            let email = userInput.value.trim();

            // Si no parece un email, asumimos que es username y buscamos en Firestore
            if (!email.includes("@")) {
                const resolvedEmail = await resolveEmailFromUsername(email);
                if (!resolvedEmail) {
                    Swal.fire({
                        icon: "error",
                        title: "Usuario no encontrado",
                        text: "Revisa tu nombre de usuario o regístrate.",
                        background: "#1f1f2e",
                        color: "#fff"
                    });
                    return;
                }
                email = resolvedEmail;
            }

            // 🔹 Iniciar sesión con Auth
            await signInWithEmailAndPassword(auth, email, passInput.value);

            Swal.fire({
                icon: "success",
                title: "Bienvenido 🎉",
                text: "Has iniciado sesión correctamente.",
                background: "#1f1f2e",
                color: "#fff",
                confirmButtonColor: "#10b981"
            }).then(() => {
                // Ajustá la ruta según tus templates
                window.location.href = "/home/index.html";
            });

        } catch (error) {
            console.error("❌ Error al iniciar sesión:", error);

            let mensaje = "Ocurrió un error inesperado.";
            if (error.code === "auth/user-not-found") {
                mensaje = "El usuario no existe.";
            } else if (error.code === "auth/wrong-password") {
                mensaje = "Contraseña incorrecta.";
            } else if (error.code === "auth/invalid-email") {
                mensaje = "Correo inválido.";
            } else if (error.code === "auth/too-many-requests") {
                mensaje = "Demasiados intentos fallidos. Intenta más tarde.";
            }

            Swal.fire({
                icon: "error",
                title: "Error al iniciar sesión",
                text: mensaje,
                background: "#1f1f2e",
                color: "#fff",
                confirmButtonColor: "#ef4444"
            });
        }
    });
});

// 🔹 Animación Shake (CSS in JS)
const style = document.createElement("style");
style.innerHTML = `
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-6px); }
  40%, 80% { transform: translateX(6px); }
}
.animate-shake {
  animation: shake 0.4s;
}
`;
document.head.appendChild(style);
