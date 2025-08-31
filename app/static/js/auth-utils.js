// auth-utils.js
import Swal from "sweetalert2";
import { db, doc, getDoc, collection, query, where, getDocs, limit } from "./firebase-config.js";

// =========================
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

// =========================
// 🔹 Animaciones y errores
export const animateError = (input) => {
  input.classList.add("border-red-500", "animate-shake");
  setTimeout(() => input.classList.remove("animate-shake"), 400);
};

export const showError = (title, message) => {
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

export const showLoading = (title = "Procesando...", text = "Por favor espera") => {
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
export const validate = {
  required: (input, msg = "Campo obligatorio") => {
    const valid = input.value.trim() !== "";
    if (!valid) animateError(input);
    return valid;
  },
  password: (input, minLength = 6) => {
    const valid = input.value.trim().length >= minLength;
    if (!valid) animateError(input);
    return valid;
  },
  email: (input) => {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const valid = pattern.test(input.value.trim());
    if (!valid) animateError(input);
    return valid;
  },
  username: (input) => {
    const valid = /^[a-zA-Z0-9-_]{3,15}$/.test(input.value.trim());
    if (!valid) animateError(input);
    return valid;
  },
  confirmPassword: (passInput, confirmInput) => {
    const valid = passInput.value.trim() === confirmInput.value.trim();
    if (!valid) animateError(confirmInput);
    return valid;
  },
  dob: (input, minAge = 13) => {
    if (!input.value) return true;
    const birthDate = new Date(input.value);
    const age = new Date().getFullYear() - birthDate.getFullYear();
    const valid = age >= minAge;
    if (!valid) animateError(input);
    return valid;
  },
  role: (input, rolesValidos) => {
    const valid = rolesValidos.includes(input.value);
    if (!valid) animateError(input);
    return valid;
  }
};

// =========================
// 🔹 Firebase helpers
export const resolveEmailFromUsername = async (username) => {
  try {
    const q = query(collection(db, "usuarios"), where("username", "==", username.trim()), limit(1));
    const snapshot = await getDocs(q);
    return !snapshot.empty ? snapshot.docs[0].data().email : null;
  } catch (err) {
    console.error("❌ Error buscando username:", err);
    return null;
  }
};

export const getUserRole = async (uid) => {
  try {
    const docRef = doc(db, "usuarios", uid);
    const docSnap = await getDoc(docRef);
    return docSnap.exists() ? (docSnap.data().role || "comprador") : "comprador";
  } catch (err) {
    console.error("❌ Error obteniendo rol:", err);
    return "comprador";
  }
};
