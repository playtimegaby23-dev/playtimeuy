// main.js — Funciones generales para PlayTimeUY

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ PlayTimeUY: JS cargado correctamente");

  // -------------------------------
  // Mostrar/Ocultar contraseña
  // -------------------------------
  document.querySelectorAll(".toggle-password").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      const type = input.type === "password" ? "text" : "password";
      input.type = type;
      btn.innerHTML = type === "password" ? "👁️" : "🙈";
    });
  });

  // -------------------------------
  // Toasts - Notificaciones visuales
  // -------------------------------
  const showToast = (message, type = "success", duration = 3000) => {
    const toast = document.createElement("div");
    toast.className = `fixed top-5 right-5 z-50 px-4 py-2 rounded-xl shadow-lg text-white text-sm font-medium transition-all ${
      type === "success" ? "bg-emerald-500" : "bg-red-500"
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("opacity-0", "translate-y-4");
      setTimeout(() => toast.remove(), 300), 300;
    }, duration);
  };

  // -------------------------------
  // Animación con IntersectionObserver
  // -------------------------------
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("animate-fade-in-up");
    });
  }, { threshold: 0.1 });

  document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

  // -------------------------------
  // Navbar transparente dinámico
  // -------------------------------
  const navbar = document.querySelector("header");
  if (navbar) {
    window.addEventListener("scroll", () => {
      navbar.classList.toggle("bg-gray-900/80", window.scrollY > 40);
      navbar.classList.toggle("backdrop-blur", window.scrollY > 40);
    });
  }

  // -------------------------------
  // Modo oscuro toggle (si lo querés usar)
  // -------------------------------
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      document.documentElement.classList.toggle("dark");
    });
  }

  // -------------------------------
  // Cierre de sesión (Firebase)
  // -------------------------------
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await firebase.auth().signOut();
        showToast("Sesión cerrada correctamente");
        setTimeout(() => (window.location.href = "/"), 1500);
      } catch (error) {
        console.error(error);
        showToast("Error al cerrar sesión", "error");
      }
    });
  }

  // -------------------------------
  // Validación rápida en formularios
  // -------------------------------
  const requiredFields = document.querySelectorAll("[required]");
  requiredFields.forEach((field) => {
    field.addEventListener("invalid", () => {
      field.classList.add("border-red-500");
    });
    field.addEventListener("input", () => {
      field.classList.remove("border-red-500");
    });
  });
});
