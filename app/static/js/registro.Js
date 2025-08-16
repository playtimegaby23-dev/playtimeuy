// registro.js
import { auth, db } from "./firebase-config.js";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registroForm");

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

    // Animación de error
    function animateError(input) {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    }

    // Validaciones
    function validateEmail(input) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
        if (!emailPattern.test(input.value.trim())) {
            animateError(input);
            return false;
        }
        return true;
    }

    function validatePassword(input) {
        if (input.value.trim().length < 6) {
            animateError(input);
            return false;
        }
        return true;
    }

    function validateConfirmPassword(passInput, confirmInput) {
        if (confirmInput.value.trim() !== passInput.value.trim()) {
            animateError(confirmInput);
            return false;
        }
        return true;
    }

    // Validación en tiempo real
    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));

    // Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (
            !validateEmail(emailInput) ||
            !validatePassword(passInput) ||
            !validateConfirmPassword(passInput, confirmInput)
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

            // Crear usuario en Auth
            const userCredential = await createUserWithEmailAndPassword(auth, emailInput.value, passInput.value);
            const user = userCredential.user;

            // Guardar datos en Firestore
            await setDoc(doc(db, "usuarios", user.uid), {
                fullName: fullNameInput.value.trim(),
                username: usernameInput.value.trim(),
                email: emailInput.value.trim(),
                dob: dobInput.value,
                country: countryInput.value.trim(),
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
                window.location.href = "/inicio";
            });

        } catch (error) {
            console.error("Error al registrar usuario:", error);
            Swal.fire({
                icon: "error",
                title: "Error al registrarse",
                text: error.message,
                background: "#1f1f2e",
                color: "#fff",
                confirmButtonColor: "#ef4444"
            });
        }
    });
});

/* Animación Shake */
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
