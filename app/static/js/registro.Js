// registro.js
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registroForm");

    // Inicializar Firebase
    const firebaseConfig = {
        apiKey: "TU_API_KEY",
        authDomain: "TU_AUTH_DOMAIN",
        projectId: "TU_PROJECT_ID",
        storageBucket: "TU_STORAGE_BUCKET",
        messagingSenderId: "TU_MESSAGING_SENDER_ID",
        appId: "TU_APP_ID"
    };

    firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    const db = firebase.firestore();

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

    // Validación en tiempo real
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
        const confirmPassword = confirmInput.value.trim();

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

            // Crear usuario en Firebase Auth
            const userCredential = await auth.createUserWithEmailAndPassword(email, password);
            const user = userCredential.user;

            // Guardar datos extra en Firestore
            await db.collection("usuarios").doc(user.uid).set({
                email: email,
                creadoEn: firebase.firestore.FieldValue.serverTimestamp()
            });

            Swal.fire("¡Registro exitoso!", "Tu cuenta ha sido creada correctamente.", "success")
                .then(() => window.location.href = "/inicio");

        } catch (error) {
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
