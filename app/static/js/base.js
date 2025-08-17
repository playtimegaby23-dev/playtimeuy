// Base.js - Funcionalidades globales PlayTimeUY (Mejorado)

document.addEventListener("DOMContentLoaded", () => {

  // 🔹 Loader Fade Out
  const loader = document.getElementById("loader");
  if (loader) {
    setTimeout(() => {
      loader.classList.add("opacity-0", "transition-opacity", "duration-700");
      loader.addEventListener("transitionend", () => loader.remove());
    }, 1200);
  }

  // 🔹 Navbar Scroll Effect
  const navbar = document.querySelector("nav");
  if (navbar) {
    const handleNavbarScroll = () => {
      if (window.scrollY > 50) {
        navbar.classList.add("bg-dark", "shadow-lg", "backdrop-blur-md");
      } else {
        navbar.classList.remove("bg-dark", "shadow-lg", "backdrop-blur-md");
      }
    };
    window.addEventListener("scroll", handleNavbarScroll);
    handleNavbarScroll(); // Inicializar al cargar
  }

  // 🔹 Smooth Scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", e => {
      const target = document.querySelector(anchor.getAttribute("href"));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  // 🔹 Animate elements on scroll
  const animatedElements = document.querySelectorAll(".animate-on-scroll");
  if (animatedElements.length > 0) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate__fadeInUp");
          entry.target.classList.remove("opacity-0");
          obs.unobserve(entry.target); // Solo animar una vez
        }
      });
    }, { threshold: 0.2 });

    animatedElements.forEach(el => {
      el.classList.add("opacity-0", "animate__animated");
      observer.observe(el);
    });
  }

  // 🔹 Función auxiliar para debounce (opcional para scroll performance)
  const debounce = (fn, delay = 100) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  };

});
