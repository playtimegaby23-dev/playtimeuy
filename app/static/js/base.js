// Base.js - PlayTimeUY v2 - Global Functions & UI Enhancements
document.addEventListener("DOMContentLoaded", () => {

  // 🔹 Loader Fade Out
  const loader = document.getElementById("loader");
  if (loader) {
    setTimeout(() => {
      loader.classList.add("opacity-0", "transition-opacity", "duration-700");
      loader.addEventListener("transitionend", () => loader.remove());
    }, 800);
  }

  // 🔹 Navbar Scroll + Mobile Menu Toggle
  const navbar = document.querySelector("nav");
  const mobileMenuBtn = document.querySelector("#mobile-menu-btn");
  const mobileMenu = document.querySelector("#mobile-menu");

  if (navbar) {
    let lastScrollY = window.scrollY;
    const updateNavbar = () => {
      if (window.scrollY > 50) {
        navbar.classList.add("bg-black/80", "shadow-lg", "backdrop-blur-md");
      } else {
        navbar.classList.remove("bg-black/80", "shadow-lg", "backdrop-blur-md");
      }
      lastScrollY = window.scrollY;
    };
    window.addEventListener("scroll", () => requestAnimationFrame(updateNavbar), { passive: true });
    updateNavbar();
  }

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
    });
  }

  // 🔹 Smooth Scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", e => {
      const target = document.querySelector(anchor.getAttribute("href"));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      mobileMenu?.classList.add("hidden");
    });
  });

  // 🔹 Prefetch external links for UX
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    link.addEventListener("mouseenter", () => {
      const prefetch = document.createElement("link");
      prefetch.rel = "prefetch";
      prefetch.href = link.href;
      document.head.appendChild(prefetch);
    }, { once: true });
  });

  // 🔹 Intersection Observer Animations
  const animatedElements = document.querySelectorAll(".animate-on-scroll");
  if (animatedElements.length > 0) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate__fadeInUp");
          entry.target.classList.remove("opacity-0");
          if (!entry.target.classList.contains("animate-repeat")) obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    animatedElements.forEach(el => {
      el.classList.add("opacity-0", "animate__animated");
      observer.observe(el);
    });
  }

  // 🔹 Debounce helper
  window.debounce = (fn, delay = 100) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  };

  // 🔹 Global Toast Notifications
  window.showToast = (msg, type = "info") => {
    const colors = { info: "bg-gray-800", success: "bg-green-600", error: "bg-red-600" };
    const el = document.createElement("div");
    el.className = `fixed bottom-6 right-6 px-4 py-2 rounded-lg text-white ${colors[type]||colors.info} z-50 shadow-lg`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  };

  // 🔹 Global fetch wrapper
  window.apiFetch = async (url, options = {}) => {
    const res = await fetch(url, { credentials: "same-origin", ...options });
    const json = await res.json();
    if (!res.ok) throw json;
    return json;
  };

  // 🔹 Modal Helper
  window.openModal = (id) => {
    const modal = document.getElementById(id);
    modal?.showModal();
  };
  window.closeModal = (id) => {
    const modal = document.getElementById(id);
    modal?.close();
  };

  // 🔹 Tabs handler (profiles, dashboard)
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      const parent = btn.closest("nav, .tabs-wrapper");
      parent?.querySelectorAll(".tab").forEach(t => t.classList.remove("active", "bg-primary", "text-white"));
      btn.classList.add("active", "bg-primary", "text-white");
      // Optional: trigger a callback if needed (e.g., reload posts)
      const tabEvent = new CustomEvent("tabChanged", { detail: { tab: btn.dataset.tab } });
      btn.dispatchEvent(tabEvent);
    });
  });

  // 🔹 Copy to clipboard (dynamic for links/buttons)
  document.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", async () => {
      try {
        const text = btn.dataset.copy;
        await navigator.clipboard.writeText(text);
        showToast("Copiado al portapapeles", "success");
      } catch {
        showToast("Error al copiar", "error");
      }
    });
  });

  // 🔹 Loader overlay for async actions
  window.showLoader = (msg = "Cargando...") => {
    let overlay = document.getElementById("global-loader");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "global-loader";
      overlay.className = "fixed inset-0 flex items-center justify-center bg-black/70 z-50";
      overlay.innerHTML = `<div class="text-white text-lg font-semibold">${msg}</div>`;
      document.body.appendChild(overlay);
    } else overlay.querySelector("div").textContent = msg;
    overlay.classList.remove("hidden");
  };
  window.hideLoader = () => {
    const overlay = document.getElementById("global-loader");
    overlay?.classList.add("hidden");
  };

});
