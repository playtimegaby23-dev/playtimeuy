// registro.js
import { auth, db } from "./firebase-config.js";
import { createUserWithEmailAndPassword, sendEmailVerification } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registroForm");
    if (!form) return console.error("❌ No se encontró el formulario con id='registroForm'");

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

    const ROLES_VALIDOS = ["buyer", "creator", "promoter", "admin"];

    function setError(input, message = "") {
        let errorSpan = input.parentNode.querySelector(".error-msg");
        if (!errorSpan) {
            errorSpan = document.createElement("span");
            errorSpan.className = "error-msg text-red-500 text-xs";
            input.parentNode.appendChild(errorSpan);
        }
        errorSpan.textContent = message;
        if (message) animateError(input);
    }

    function animateError(input) {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    }

    function validateEmail(input) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        const valid = pattern.test(input.value.trim());
        setError(input, valid ? "" : "Correo electrónico inválido");
        return valid;
    }

    function validatePassword(input) {
        const v = input.value.trim();
        const valid = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/.test(v);
        setError(input, valid ? "" : "Contraseña: 8+ caracteres, mayúscula, número y símbolo");
        return valid;
    }

    function validateConfirmPassword(passInput, confirmInput) {
        const valid = passInput.value.trim() === confirmInput.value.trim();
        setError(confirmInput, valid ? "" : "Las contraseñas no coinciden");
        return valid;
    }

    function validateRequired(input, msg = "Campo obligatorio") {
        const valid = input.value.trim() !== "";
        setError(input, valid ? "" : msg);
        return valid;
    }

    function validateUsername(input) {
        const valid = /^[a-zA-Z0-9-_]{3,15}$/.test(input.value.trim());
        setError(input, valid ? "" : "Usuario: 3-15 caracteres, letras/números/guiones");
        return valid;
    }

    function validateDOB(input) {
        if (!input.value) return true;
        const birthDate = new Date(input.value);
        const age = new Date().getFullYear() - birthDate.getFullYear();
        const valid = age >= 13;
        setError(input, valid ? "" : "Debes tener mínimo 13 años");
        return valid;
    }

    function validateRole(input) {
        const valid = ROLES_VALIDOS.includes(input.value);
        setError(input, valid ? "" : "Rol inválido");
        return valid;
    }

    // Validación en tiempo real
    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));
    usernameInput.addEventListener("input", () => validateUsername(usernameInput));

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateEmail(emailInput) ||
            !validatePassword(passInput) ||
            !validateConfirmPassword(passInput, confirmInput) ||
            !validateRequired(fullNameInput) ||
            !validateUsername(usernameInput) ||
            !validateDOB(dobInput) ||
            !validateRole(roleInput)) {
            Swal.fire("Error", "Corrige los errores antes de continuar.", "error");
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

            const userCredential = await createUserWithEmailAndPassword(auth, emailInput.value, passInput.value);
            const user = userCredential.user;

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

            // 🔹 Enviar correo de verificación
            await sendEmailVerification(user);

            Swal.fire({
                icon: "success",
                title: "¡Registro exitoso!",
                html: "Revisa tu correo para verificar tu cuenta.",
                background: "#1f1f2e",
                color: "#fff",
                confirmButtonColor: "#ec4899"
            }).then(() => {
                switch (roleInput.value) {
                    case "buyer": window.location.href = "/users/buyer"; break;
                    case "creator": window.location.href = "/creators/perfil_creator"; break;
                    case "promoter": window.location.href = "/users/promoter"; break;
                    case "admin": window.location.href = "/admin/admindashboard"; break;
                    default: window.location.href = "/home/index";
                }
            });

        } catch (error) {
            console.error("Error al registrar usuario:", error);
            let mensaje = "Ocurrió un error inesperado.";
            switch (error.code) {
                case "auth/email-already-in-use": mensaje = "El correo ya está registrado."; break;
                case "auth/invalid-email": mensaje = "Correo no válido."; break;
                case "auth/weak-password": mensaje = "Contraseña débil."; break;
                case "auth/too-many-requests": mensaje = "Demasiados intentos, intenta más tarde."; break;
                case "auth/network-request-failed": mensaje = "Error de red, revisa tu conexión."; break;
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

// 🔹 Animación Shake
const style = document.createElement("style");
style.innerHTML = `
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-6px); }
  40%, 80% { transform: translateX(6px); }
}
.animate-shake { animation: shake 0.4s; }
`;
document.head.appendChild(style);
