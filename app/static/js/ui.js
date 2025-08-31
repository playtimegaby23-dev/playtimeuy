// ui.js
import Swal from "sweetalert2";

export const showLoading = () => {
    Swal.fire({
        title: "Creando tu cuenta...",
        text: "Estamos registrando tus datos",
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading(),
        background: "#1f1f2e",
        color: "#fff"
    });
};

export const showSuccess = (role) => {
    Swal.fire({
        icon: "success",
        title: "¡Registro exitoso!",
        html: "Revisa tu correo para verificar tu cuenta.",
        background: "#1f1f2e",
        color: "#fff",
        confirmButtonColor: "#ec4899"
    }).then(() => {
        switch (role) {
            case "buyer": window.location.href = "/users/buyer"; break;
            case "creator": window.location.href = "/creators/perfil_creator"; break;
            case "promoter": window.location.href = "/users/promoter"; break;
            case "admin": window.location.href = "/admin/admindashboard"; break;
            default: window.location.href = "/home/index";
        }
    });
};

export const showError = (mensaje) => {
    Swal.fire({
        icon: "error",
        title: "Error al registrarse",
        text: mensaje,
        background: "#1f1f2e",
        color: "#fff",
        confirmButtonColor: "#ef4444"
    });
};
