// registro.js
import { auth, db } from "./firebase-config.js";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registroForm");

    // Mostrar/ocultar contraseñas
    document.querySelectorAll("[data-toggle]").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-toggle");
            const input = document.getElementById(id);
            if (input) {
                input.type = input.type === "password" ? "text" : "password";
                btn.classList.toggle("text-primary");
            }
        });
    });

    // Inputs y validaciones
    const emailInput = document.getElementById("email");
    const passInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm_password");

    emailInput.addEventListener("input", () => validateEmail(emailInput));
    passInput.addEventListener("input", () => validatePassword(passInput));
    confirmInput.addEventListener("input", () => validateConfirmPassword(passInput, confirmInput));

    // Envío del formulario
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passInput.value.trim();

        if (!validateEmail(emailInput) || !validatePassword(passInput) || !validateConfirmPassword(passInput, confirmInput)) {
            Swal.fire("Error", "Por favor corrige los errores antes de continuar.", "error");
            return;
        }

        try {
            // Animación de carga
            Swal.fire({
                title: "Registrando...",
                text: "Por favor espera",
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            // Crear usuario en Auth
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;

            // Guardar datos en Firestore
            await setDoc(doc(db, "usuarios", user.uid), {
                email,
                creadoEn: serverTimestamp()
            });

            Swal.fire("¡Registro exitoso!", "Tu cuenta ha sido creada correctamente.", "success")
                .then(() => window.location.href = "/inicio");

        } catch (error) {
            console.error("Error al registrar usuario:", error);
            Swal.fire("Error", error.message, "error");
        }
    });

    // Funciones de validación
    function validateEmail(input) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
        if (!emailPattern.test(input.value.trim())) {
            input.classList.add("border-red-500");
            return false;
        }
        input.classList.remove("border-red-500");
        return true;
    }

    function validatePassword(input) {
        if (input.value.trim().length < 6) {
            input.classList.add("border-red-500");
            return false;
        }
        input.classList.remove("border-red-500");
        return true;
    }

    function validateConfirmPassword(passInput, confirmInput) {
        if (confirmInput.value.trim() !== passInput.value.trim()) {
            confirmInput.classList.add("border-red-500");
            return false;
        }
        confirmInput.classList.remove("border-red-500");
        return true;
    }
});
