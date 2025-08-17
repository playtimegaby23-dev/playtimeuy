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

    // Roles permitidos
    const ROLES_VALIDOS = ["comprador", "vendedor", "creator", "admin", "promotor"];

    // Añade un span debajo de cada input para errores
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

    // 🔹 Animación de error
    function animateError(input) {
        input.classList.add("border-red-500", "animate-shake");
        setTimeout(() => input.classList.remove("animate-shake"), 400);
    }

    // 🔹 Validaciones
    function validateEmail(input) {
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        const isValid = emailPattern.test(input.value.trim());
        setError(input, isValid ? "" : "Correo electrónico inválido");
        return isValid;
    }

    function validatePassword(input) {
        const value = input.value.trim();
        const isValid = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/.test(value);
        setError(input, isValid ? "" : "La contraseña debe tener 8+ caracteres, mayúscula, número y símbolo");
        return isValid;
    }

    function validateConfirmPassword(passInput, confirmInput) {
        const isValid = confirmInput.value.trim() === passInput.value.trim();
        setError(confirmInput, isValid ? "" : "Las contraseñas no coinciden");
        return isValid;
    }

    function validateRequired(input, msg = "Campo obligatorio") {
        const isValid = input.value.trim() !== "";
        setError(input, isValid ? "" : msg);
        return isValid;
    }

    function validateUsername(input) {
        const value = input.value.trim();
        const isValid = /^[a-zA-Z0-9-_]{3,15}$/.test(value);
        setError(input, isValid ? "" : "Usuario: 3-15 caracteres, letras/números/guiones");
        return isValid;
    }

    function validateDOB(input) {
        if (!input.value) return true;
        const birthDate = new Date(input.value);
        const age = new Date().getFullYear() - birthDate.getFullYear();
        const isValid = age >= 13;
        setError(input, isValid ? "" : "Debes tener mínimo 13 años");
        return isValid;
    }

    function validateRole(input) {
        const isValid = ROLES_VALIDOS.includes(input.value);
        setError(input, isValid ? "" : "Rol inválido");
        return isValid;
    }

    // 🔹 Validación en tiempo real
    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));
    usernameInput.addEventListener("input", () => validateUsername(usernameInput));

    // 🔹 Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (
            !validateEmail(emailInput) ||
            !validatePassword(passInput) ||
            !validateConfirmPassword(passInput, confirmInput) ||
            !validateRequired(fullNameInput) ||
            !validateUsername(usernameInput) ||
            !validateDOB(dobInput) ||
            !validateRole(roleInput)
        ) {
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
                // 🔹 Redirección según rol
                switch (roleInput.value) {
                    case "comprador": window.location.href = "/users/comprador"; break;
                    case "vendedor": window.location.href = "/users/vendedor"; break;
                    case "creator": window.location.href = "/creators/perfil_creator"; break;
                    case "admin": window.location.href = "/admin/admindashboard"; break;
                    case "promotor": window.location.href = "/users/promotor"; break;
                    default: window.location.href = "/home/index";
                }
            });

        } catch (error) {
            console.error("Error al registrar usuario:", error);

            let mensaje = "Ocurrió un error inesperado.";
            switch (error.code) {
                case "auth/email-already-in-use": mensaje = "El correo ya está registrado."; break;
                case "auth/invalid-email": mensaje = "El correo no es válido."; break;
                case "auth/weak-password": mensaje = "La contraseña es demasiado débil."; break;
                case "auth/too-many-requests": mensaje = "Demasiados intentos, intenta más tarde."; break;
                case "auth/network-request-failed": mensaje = "Error de red. Revisa tu conexión."; break;
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
