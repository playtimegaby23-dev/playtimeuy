// index.js - PlayTimeUY
// Script profesional con animaciones y navegación dinámica ✨

document.addEventListener("DOMContentLoaded", () => {
  initNavbarHighlight();
  initScrollAnimations();
  initBackToTop();
  initLoader();
});

/* -------------------------------
   NAVBAR: marcar la página activa
---------------------------------*/
function initNavbarHighlight() {
  const currentPath = window.location.pathname;
  document.querySelectorAll("nav a").forEach(link => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add(
        "text-pink-500",
        "font-bold",
        "border-b-2",
        "border-pink-500"
      );
    } else {
      link.classList.remove("text-pink-500", "font-bold", "border-b-2", "border-pink-500");
    }
  });
}

/* -------------------------------
   SCROLL ANIMATIONS: fade + slide
---------------------------------*/
function initScrollAnimations() {
  const animatedElements = document.querySelectorAll(".animate-on-scroll");

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add(
          "opacity-100",
          "translate-y-0",
          "transition-all",
          "duration-1000",
          "ease-out"
        );
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  animatedElements.forEach(el => {
    el.classList.add("opacity-0", "translate-y-10");
    observer.observe(el);
  });
}

/* -------------------------------
   BACK TO TOP BUTTON
---------------------------------*/
function initBackToTop() {
  const btn = document.createElement("button");
  btn.innerHTML = "⬆";
  btn.className =
    "fixed bottom-6 right-6 bg-pink-600 text-white rounded-full p-3 shadow-lg opacity-0 pointer-events-none transition duration-500 hover:bg-pink-700";
  document.body.appendChild(btn);

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      btn.classList.remove("opacity-0", "pointer-events-none");
      btn.classList.add("opacity-100");
    } else {
      btn.classList.add("opacity-0", "pointer-events-none");
    }
  });

  btn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

/* -------------------------------
   LOADER DE INICIO (opcional)
---------------------------------*/
function initLoader() {
  const loader = document.getElementById("loader");
  if (!loader) return;

  setTimeout(() => {
    loader.classList.add("opacity-0", "transition-opacity", "duration-700");
    setTimeout(() => loader.remove(), 700);
  }, 800);
}
