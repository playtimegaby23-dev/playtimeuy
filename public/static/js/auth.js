// auth.js

// Firebase Config (reemplazada automáticamente por variables desde entorno Python/Jinja si usás Flask)
const firebaseConfig = {
    apiKey: "AIzaSyD8cKZyxIvZ6Uq3W7y2cUJdyteZGUdtNNg",
    authDomain: "playtimeuy.firebaseapp.com",
    projectId: "playtimeuy",
    storageBucket: "playtimeuy.appspot.com",
    messagingSenderId: "709385694606",
    appId: "1:709385694606:web:7e6ff7ff52bcaba9cf48df"
};

// Inicializar Firebase solo una vez
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}
const auth = firebase.auth();
const provider = new firebase.auth.GoogleAuthProvider();

// ==============================
// Google Login
// ==============================
document.addEventListener('DOMContentLoaded', () => {
    const googleBtn = document.getElementById("google-login");

    if (googleBtn) {
        googleBtn.addEventListener("click", (e) => {
            e.preventDefault();
            auth.signInWithPopup(provider)
                .then(result => {
                    const user = result.user;
                    if (user.emailVerified || user.providerData[0].providerId === 'google.com') {
                        // Redireccionar al backend para gestionar sesión
                        fetch('/login/google', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ idToken: user.za })  // user.getIdToken() no está disponible directamente aquí
                        })
                        .then(res => {
                            if (res.redirected) {
                                window.location.href = res.url;
                            } else {
                                alert("Inicio de sesión con Google exitoso, pero algo salió mal en el servidor.");
                            }
                        });
                    } else {
                        alert("Tu correo debe estar verificado.");
                        auth.signOut();
                    }
                })
                .catch(error => {
                    console.error("Error en login con Google:", error);
                    alert("Error al iniciar sesión con Google.");
                });
        });
    }
});
