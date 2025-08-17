import { auth, db, doc, getDoc, collection, query, where, getDocs } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "firebase/auth";
import Swal from "sweetalert2";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    if (!form) return console.error("❌ No se encontró el formulario con id='loginForm'");

    const userInput = form.querySelector("input[name='user']"); // email o username
    const passInput = form.querySelector("input[name='password']");

    // 🔹 Animación de error
    const animateError = (input) => {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    };

    // 🔹 Validaciones
    const validateRequired = (input) => {
        const valid = input.value.trim() !== "";
        if (!valid) animateError(input);
        return valid;
    };

    const validatePassword = (input) => {
        const valid = input.value.trim().length >= 6;
        if (!valid) animateError(input);
        return valid;
    };

    // 🔹 Validación en tiempo real
    userInput.addEventListener("input", () => validateRequired(userInput));
    passInput.addEventListener("input", () => validatePassword(passInput));

    // 🔹 Obtener email desde username
    const resolveEmailFromUsername = async (username) => {
        try {
            const q = query(collection(db, "usuarios"), where("username", "==", username.trim()));
            const snapshot = await getDocs(q);
            if (!snapshot.empty) return snapshot.docs[0].data().email;
            return null;
        } catch (err) {
            console.error("❌ Error buscando username:", err);
            return null;
        }
    };

    // 🔹 Obtener rol del usuario
    const getUserRole = async (uid) => {
        try {
            const docRef = doc(db, "usuarios", uid);
            const docSnap = await getDoc(docRef);
            return docSnap.exists() ? docSnap.data().role : null;
        } catch (err) {
            console.error("❌ Error obteniendo rol:", err);
            return null;
        }
    };

    // 🔹 Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateRequired(userInput) || !validatePassword(passInput)) {
            return Swal.fire("Error", "Por favor completa todos los campos correctamente.", "error");
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

            // Si no es email, buscar por username
            if (!email.includes("@")) {
                const resolvedEmail = await resolveEmailFromUsername(email);
                if (!resolvedEmail) {
                    return Swal.fire({
                        icon: "error",
                        title: "Usuario no encontrado",
                        text: "Revisa tu nombre de usuario o regístrate.",
                        background: "#1f1f2e",
                        color: "#fff"
                    });
                }
                email = resolvedEmail;
            }

            // 🔹 Login con Firebase Auth
            const userCredential = await signInWithEmailAndPassword(auth, email, passInput.value);
            const user = userCredential.user;

            // 🔹 Obtener rol
            const role = await getUserRole(user.uid);

            Swal.close();

            // 🔹 Redirección según rol
            switch (role) {
                case "comprador": window.location.href = "/users/comprador"; break;
                case "vendedor": window.location.href = "/users/vendedor"; break;
                case "creator": window.location.href = "/creators/perfil_creator"; break;
                case "admin": window.location.href = "/admin/admindashboard"; break;
                case "promotor": window.location.href = "/users/promotor"; break;
                default: window.location.href = "/home/index"; break;
            }

        } catch (error) {
            console.error("❌ Error al iniciar sesión:", error);
            let mensaje = "Ocurrió un error inesperado.";
            if (error.code === "auth/user-not-found") mensaje = "El usuario no existe.";
            else if (error.code === "auth/wrong-password") mensaje = "Contraseña incorrecta.";
            else if (error.code === "auth/invalid-email") mensaje = "Correo inválido.";
            else if (error.code === "auth/too-many-requests") mensaje = "Demasiados intentos fallidos. Intenta más tarde.";

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

// 🔹 Animación Shake (CSS)
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
