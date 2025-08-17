// registro.js
import { auth, db } from "./firebase-config.js";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registroForm");
    if (!form) {
        console.error("❌ No se encontró el formulario con id='registroForm'");
        return;
    }

    // Inputs
    const emailInput = form.querySelector("input[name='email']");
    const passInput = form.querySelector("input[name='password']");
    const confirmInput = form.querySelector("input[name='confirm_password']");
    const fullNameInput = form.querySelector("input[name='full_name']");
    const usernameInput = form.querySelector("input[name='username']");
    const dobInput = form.querySelector("input[name='dob']");
    const countryInput = form.querySelector("input[name='country']");
    const twitterInput = form.querySelector("input[name='twitter']");
    const instagramInput = form.querySelector("input[name='instagram']");
    const roleInput = form.querySelector("select[name='role']");

    // 🔹 Animación de error
    function animateError(input) {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    }

    // 🔹 Validaciones
    function validateEmail(input) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
        const isValid = emailPattern.test(input.value.trim());
        if (!isValid) animateError(input);
        return isValid;
    }

    function validatePassword(input) {
        const value = input.value.trim();
        // 🔹 Contraseña más fuerte: mínimo 6 caracteres
        const isValid = value.length >= 6;
        if (!isValid) animateError(input);
        return isValid;
    }

    function validateConfirmPassword(passInput, confirmInput) {
        const isValid = confirmInput.value.trim() === passInput.value.trim();
        if (!isValid) animateError(confirmInput);
        return isValid;
    }

    function validateRequired(input) {
        const isValid = input.value.trim() !== "";
        if (!isValid) animateError(input);
        return isValid;
    }

    // 🔹 Validación en tiempo real
    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));

    // 🔹 Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (
            !validateEmail(emailInput) ||
            !validatePassword(passInput) ||
            !validateConfirmPassword(passInput, confirmInput) ||
            !validateRequired(fullNameInput) ||
            !validateRequired(usernameInput) ||
            !validateRequired(roleInput)
        ) {
            Swal.fire("Error", "Por favor corrige los errores antes de continuar.", "error");
            return;
        }

        try {
            Swal.fire({
                title: "Creando tu cuenta...",
                text: "Estamos registrando tus datos",
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading(),
                background: "#1f1f2e",
                color: "#fff"
            });

            // 🔹 Crear usuario en Auth
            const userCredential = await createUserWithEmailAndPassword(auth, emailInput.value, passInput.value);
            const user = userCredential.user;

            // 🔹 Guardar datos en Firestore
            await setDoc(doc(db, "usuarios", user.uid), {
                fullName: fullNameInput.value.trim(),
                username: usernameInput.value.trim(),
                email: emailInput.value.trim(),
                dob: dobInput.value || null,
                country: countryInput.value.trim() || null,
                twitter: twitterInput.value.trim() || null,
                instagram: instagramInput.value.trim() || null,
                role: roleInput.value,
                creadoEn: serverTimestamp()
            });

            Swal.fire({
                icon: "success",
                title: "¡Registro exitoso!",
                text: "Tu cuenta ha sido creada correctamente.",
                background: "#1f1f2e",
                color: "#fff",
                confirmButtonColor: "#ec4899"
            }).then(() => {
                // 🔹 Redirección (ajusta la ruta según tu proyecto)
                window.location.href = "/inicio";
            });

        } catch (error) {
            console.error("Error al registrar usuario:", error);

            let mensaje = "Ocurrió un error inesperado.";
            if (error.code === "auth/email-already-in-use") {
                mensaje = "El correo ya está registrado.";
            } else if (error.code === "auth/invalid-email") {
                mensaje = "El correo no es válido.";
            } else if (error.code === "auth/weak-password") {
                mensaje = "La contraseña es demasiado débil.";
            }

            Swal.fire({
                icon: "error",
                title: "Error al registrarse",
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
