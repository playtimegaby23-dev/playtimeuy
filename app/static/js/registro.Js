// =============================
// PlayTimeUY - Registro de usuarios
// =============================

import { auth, db } from "./firebase-config.js";
import { createUserWithEmailAndPassword, sendEmailVerification } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

import {
    validateEmail, validatePassword, validateConfirmPassword,
    validateRequired, validateUsername, validateDOB, validateRole,
    injectShakeAnimation
} from "./validators.js";

import { showLoading, showSuccess, showError } from "./ui.js";

document.addEventListener("DOMContentLoaded", () => {
    injectShakeAnimation();

    const form = document.getElementById("registroForm");
    if (!form) return console.error("❌ No se encontró el formulario con id='registroForm'");

    const emailInput     = form.querySelector("input[name='email']");
    const passInput      = form.querySelector("input[name='password']");
    const confirmInput   = form.querySelector("input[name='confirm_password']");
    const fullNameInput  = form.querySelector("input[name='full_name']");
    const usernameInput  = form.querySelector("input[name='username']");
    const dobInput       = form.querySelector("input[name='dob']");
    const countryInput   = form.querySelector("input[name='country']");
    const twitterInput   = form.querySelector("input[name='twitter']");
    const instagramInput = form.querySelector("input[name='instagram']");
    const roleInput      = form.querySelector("select[name='role']");
    const submitBtn      = form.querySelector("button[type='submit']");

    // ✅ Validación en tiempo real
    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));
    usernameInput.addEventListener("input", () => validateUsername(usernameInput));

    // =============================
    // Envío del formulario
    // =============================
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Validar todos los campos
        const valid =
            validateEmail(emailInput) &&
            validatePassword(passInput) &&
            validateConfirmPassword(passInput, confirmInput) &&
            validateRequired(fullNameInput) &&
            validateUsername(usernameInput) &&
            validateDOB(dobInput) &&
            validateRole(roleInput);

        if (!valid) {
            Swal.fire("Error", "Corrige los errores antes de continuar.", "error");
            const firstError = form.querySelector(".border-red-500");
            if (firstError) firstError.focus();
            return;
        }

        try {
            showLoading();
            submitBtn.disabled = true; // evita doble submit

            // Crear usuario en Firebase Auth
            const userCredential = await createUserWithEmailAndPassword(
                auth,
                emailInput.value.trim(),
                passInput.value.trim()
            );
            const user = userCredential.user;

            // Guardar datos en Firestore
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

            // Enviar verificación
            await sendEmailVerification(user);

            showSuccess(roleInput.value);
            form.reset();

        } catch (error) {
            console.error("❌ Error al registrar usuario:", error);
            let mensaje = "Ocurrió un error inesperado.";
            switch (error.code) {
                case "auth/email-already-in-use": mensaje = "El correo ya está registrado."; break;
                case "auth/invalid-email": mensaje = "Correo no válido."; break;
                case "auth/weak-password": mensaje = "Contraseña débil."; break;
                case "auth/too-many-requests": mensaje = "Demasiados intentos, intenta más tarde."; break;
                case "auth/network-request-failed": mensaje = "Error de red, revisa tu conexión."; break;
            }
            showError(mensaje);
        } finally {
            submitBtn.disabled = false;
        }
    });
});
