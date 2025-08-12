// main.js — Funciones generales para PlayTimeUY

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ PlayTimeUY: JS cargado correctamente");

  // -------------------------------
  // Mostrar/Ocultar contraseña
  // -------------------------------
  document.querySelectorAll(".toggle-password").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      // Cambiar icono con emojis accesibles (podés reemplazar con SVG si querés)
      btn.textContent = isPassword ? "🙈" : "👁️";
      btn.setAttribute("aria-label", isPassword ? "Ocultar contraseña" : "Mostrar contraseña");
    });
  });

  // -------------------------------
  // Toasts - Notificaciones visuales
  // -------------------------------
  const showToast = (message, type = "success", duration = 3000) => {
    const toast = document.createElement("div");
    toast.className = `fixed top-5 right-5 z-50 max-w-xs px-4 py-2 rounded-xl shadow-lg text-white text-sm font-medium transition-transform duration-300 ease-in-out
      ${type === "success" ? "bg-emerald-500" : type === "warning" ? "bg-yellow-500" : "bg-red-500"}`;
    toast.textContent = message;
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(1rem)";
      toast.addEventListener("transitionend", () => toast.remove());
    }, duration);
  };

  // Ejemplo para probar
  // showToast("Bienvenido a PlayTimeUY!");

  // -------------------------------
  // Animación con IntersectionObserver
  // -------------------------------
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-fade-in-up");
          observer.unobserve(entry.target); // Solo animar una vez
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
  } else {
    // Fallback: mostrar todos sin animación
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("animate-fade-in-up"));
  }

  // -------------------------------
  // Navbar transparente dinámico
  // -------------------------------
  const navbar = document.querySelector("header");
  if (navbar) {
    const scrollHandler = () => {
      const scrolled = window.scrollY > 40;
      navbar.classList.toggle("bg-gray-900/80", scrolled);
      navbar.classList.toggle("backdrop-blur", scrolled);
      navbar.classList.toggle("border-b", scrolled);
      navbar.classList.toggle("border-white/10", scrolled);
    };
    window.addEventListener("scroll", scrollHandler);
    scrollHandler(); // Ejecutar al cargar para estado inicial
  }

  // -------------------------------
  // Modo oscuro toggle (opcional)
  // -------------------------------
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const isDark = document.documentElement.classList.toggle("dark");
      localStorage.setItem("theme", isDark ? "dark" : "light");
    });

    // Aplicar tema guardado
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.documentElement.classList.add("dark");
    }
  }

  // -------------------------------
  // Cierre de sesión (Firebase)
  // -------------------------------
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn && window.firebase && firebase.auth) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await firebase.auth().signOut();
        showToast("Sesión cerrada correctamente", "success");
        setTimeout(() => (window.location.href = "/"), 1500);
      } catch (error) {
        console.error("Error al cerrar sesión:", error);
        showToast("Error al cerrar sesión", "error");
      }
    });
  }

  // -------------------------------
  // Validación rápida en formularios
  // -------------------------------
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const invalidFields = [];
      form.querySelectorAll("[required]").forEach((field) => {
        if (!field.value.trim()) {
          invalidFields.push(field);
          field.classList.add("border-red-500", "focus:ring-red-500");
        } else {
          field.classList.remove("border-red-500", "focus:ring-red-500");
        }
      });
      if (invalidFields.length > 0) {
        e.preventDefault();
        invalidFields[0].focus();
        showToast("Por favor completa los campos obligatorios", "warning");
      }
    });
  });

  // Quitar borde rojo al corregir campo
  document.querySelectorAll("[required]").forEach((field) => {
    field.addEventListener("input", () => {
      if (field.value.trim()) {
        field.classList.remove("border-red-500", "focus:ring-red-500");
      }
    });
  });
});
