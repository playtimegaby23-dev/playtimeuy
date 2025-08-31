// validators.js
export const ROLES_VALIDOS = ["buyer", "creator", "promoter", "admin"];

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

// ✅ Validaciones
export const validateEmail = (input) => {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const valid = pattern.test(input.value.trim());
    setError(input, valid ? "" : "Correo electrónico inválido");
    return valid;
};

export const validatePassword = (input) => {
    const v = input.value.trim();
    const valid = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/.test(v);
    setError(input, valid ? "" : "Contraseña: 8+ caracteres, mayúscula, número y símbolo");
    return valid;
};

export const validateConfirmPassword = (passInput, confirmInput) => {
    const valid = passInput.value.trim() === confirmInput.value.trim();
    setError(confirmInput, valid ? "" : "Las contraseñas no coinciden");
    return valid;
};

export const validateRequired = (input, msg = "Campo obligatorio") => {
    const valid = input.value.trim() !== "";
    setError(input, valid ? "" : msg);
    return valid;
};

export const validateUsername = (input) => {
    const valid = /^[a-zA-Z0-9-_]{3,15}$/.test(input.value.trim());
    setError(input, valid ? "" : "Usuario: 3-15 caracteres, letras/números/guiones");
    return valid;
};

export const validateDOB = (input) => {
    if (!input.value) return true;
    const birthDate = new Date(input.value);
    const age = new Date().getFullYear() - birthDate.getFullYear();
    const valid = age >= 13;
    setError(input, valid ? "" : "Debes tener mínimo 13 años");
    return valid;
};

export const validateRole = (input) => {
    const valid = ROLES_VALIDOS.includes(input.value);
    setError(input, valid ? "" : "Rol inválido");
    return valid;
};

// 🔹 Insertar animación Shake CSS globalmente (una vez)
export function injectShakeAnimation() {
    if (document.getElementById("shake-style")) return;
    const style = document.createElement("style");
    style.id = "shake-style";
    style.innerHTML = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      20%, 60% { transform: translateX(-6px); }
      40%, 80% { transform: translateX(6px); }
    }
    .animate-shake { animation: shake 0.4s; }
    `;
    document.head.appendChild(style);
}
