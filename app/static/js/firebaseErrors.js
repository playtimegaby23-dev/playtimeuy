// firebaseErrors.js
// 🔹 Diccionario de errores de Firebase traducidos al español

export function getFirebaseErrorMessage(error) {
    const errorMap = {
        // Autenticación con Email/Password
        "auth/email-already-in-use": "Este correo ya está registrado.",
        "auth/invalid-email": "El correo ingresado no es válido.",
        "auth/operation-not-allowed": "El inicio de sesión con este método está deshabilitado.",
        "auth/weak-password": "La contraseña es demasiado débil. Usa al menos 6 caracteres.",
        "auth/missing-password": "Debes ingresar una contraseña.",
        "auth/user-disabled": "Esta cuenta ha sido deshabilitada.",
        "auth/user-not-found": "No existe un usuario con este correo.",
        "auth/wrong-password": "La contraseña ingresada es incorrecta.",

        // Google / OAuth
        "auth/popup-closed-by-user": "Cerraste la ventana de inicio de sesión antes de completar.",
        "auth/cancelled-popup-request": "Ya hay una ventana emergente abierta. Cierra la otra para continuar.",
        "auth/popup-blocked": "El navegador bloqueó la ventana de inicio de sesión. Habilítala para continuar.",
        "auth/account-exists-with-different-credential": "Ya existe una cuenta con otro método de inicio de sesión.",
        "auth/credential-already-in-use": "Las credenciales ya están en uso por otra cuenta.",
        "auth/invalid-credential": "Las credenciales no son válidas o han caducado.",

        // Errores de red / conexión
        "auth/network-request-failed": "Error de conexión. Verifica tu internet.",
        "auth/timeout": "La solicitud tardó demasiado. Intenta nuevamente.",

        // Multi-factor (MFA)
        "auth/multi-factor-auth-required": "Se requiere verificación adicional (MFA).",

        // Por defecto
        "default": "Ha ocurrido un error inesperado. Intenta nuevamente."
    };

    return errorMap[error.code] || error.message || errorMap["default"];
}
