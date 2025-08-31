// login.js - Versión modular mejorada
import { auth, db, doc, getDoc, collection, query, where, getDocs, limit } from "./firebase-config.js";
import { signInWithEmailAndPassword } from "firebase/auth";
import Swal from "sweetalert2";

// =========================
// 🔹 Utilidades Generales
// =========================
const animateError = (input) => {
  input.classList.add("border-red-500", "animate-shake");
  setTimeout(() => input.classList.remove("animate-shake"), 400);
};

const showError = (title, message) => {
  Swal.fire({
    icon: "error",
    title,
    text: message,
    background: "#1f1f2e",
    color: "#fff",
    confirmButtonColor: "#ef4444",
    showClass: { popup: "animate__animated animate__shakeX" },
  });
};

const showLoading = (title = "Procesando...", text = "Por favor espera") => {
  Swal.fire({
    title,
    text,
    allowOutsideClick: false,
    didOpen: () => Swal.showLoading(),
    background: "#1f1f2e",
    color: "#fff",
  });
};

// =========================
// 🔹 Validaciones
// =========================
const validate = {
  required: (input) => {
    const valid = input.value.trim() !== "";
    if (!valid) animateError(input);
    return valid;
  },
  password: (input) => {
    const valid = input.value.trim().length >= 6;
    if (!valid) animateError(input);
    return valid;
  },
};

// =========================
// 🔹 Firebase Helpers
// =========================
const resolveEmailFromUsername = async (username) => {
  try {
    const q = query(collection(db, "usuarios"), where("username", "==", username.trim()), limit(1));
    const snapshot = await getDocs(q);
    return !snapshot.empty ? snapshot.docs[0].data().email : null;
  } catch (err) {
    console.error("❌ Error buscando username:", err);
    return null;
  }
};

const getUserRole = async (uid) => {
  try {
    const docRef = doc(db, "usuarios", uid);
    const docSnap = await getDoc(docRef);
    return docSnap.exists() ? (docSnap.data().role || "comprador") : "comprador";
  } catch (err) {
    console.error("❌ Error obteniendo rol:", err);
    return "comprador";
  }
};

// =========================
// 🔹 Inicialización
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  if (!form) return console.error("❌ No se encontró el formulario con id='loginForm'");

  const userInput = form.querySelector("input[name='user']");
  const passInput = form.querySelector("input[name='password']");

  let failedAttempts = 0;

  // 🔹 Validación en tiempo real
  userInput.addEventListener("input", () => validate.required(userInput));
  passInput.addEventListener("input", () => validate.password(passInput));

  // 🔹 Toggle de contraseña
  const toggleBtn = document.createElement("button");
  toggleBtn.type = "button";
  toggleBtn.innerText = "👁️";
  toggleBtn.className = "ml-2 text-gray-400 hover:text-white transition";
  passInput.insertAdjacentElement("afterend", toggleBtn);

  toggleBtn.addEventListener("click", () => {
    passInput.type = passInput.type === "password" ? "text" : "password";
    toggleBtn.innerText = passInput.type === "password" ? "👁️" : "🙈";
  });

  // =========================
  // 🔹 Envío del formulario
  // =========================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validate.required(userInput) || !validate.password(passInput)) {
      return showError("Error", "Por favor completa todos los campos correctamente.");
    }

    try {
      showLoading("Iniciando sesión...", "Verificando tus credenciales");

      let email = userInput.value.trim();

      // Si no es email, buscar por username
      if (!email.includes("@")) {
        const resolvedEmail = await resolveEmailFromUsername(email);
        if (!resolvedEmail) {
          Swal.close();
          return showError("Usuario no encontrado", "Revisa tu nombre de usuario o regístrate.");
        }
        email = resolvedEmail;
      }

      // 🔹 Login con Firebase Auth
      const { user } = await signInWithEmailAndPassword(auth, email, passInput.value);

      // 🔹 Obtener rol
      const role = await getUserRole(user.uid);

      Swal.close();
      failedAttempts = 0; // resetear intentos fallidos

      // 🔹 Redirección según rol
      const routes = {
        comprador: "/users/comprador",
        vendedor: "/users/vendedor",
        creator: "/creators/perfil_creator",
        admin: "/admin/admindashboard",
        promotor: "/users/promotor",
      };
      window.location.href = routes[role] || "/home/index";

    } catch (error) {
      failedAttempts++;
      console.error("❌ Error al iniciar sesión:", error);

      let mensaje = "Ocurrió un error inesperado.";
      switch (error.code) {
        case "auth/user-not-found": mensaje = "El usuario no existe."; break;
        case "auth/wrong-password": mensaje = "Contraseña incorrecta."; break;
        case "auth/invalid-email": mensaje = "Correo inválido."; break;
        case "auth/too-many-requests": mensaje = "Demasiados intentos fallidos. Intenta más tarde."; break;
      }

      if (failedAttempts >= 3 && error.code !== "auth/too-many-requests") {
        mensaje += " ⚠️ Si fallas demasiadas veces tu cuenta será bloqueada temporalmente.";
      }

      showError("Error al iniciar sesión", mensaje);
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
.animate-shake { animation: shake 0.4s; }
`;
document.head.appendChild(style);
