// base.js - Funciones globales y animaciones de PlayTimeUY
document.addEventListener("DOMContentLoaded", () => {
  // -------------------------------
  // 1️⃣ Loader fade-out con GSAP
  // -------------------------------
  const loader = document.getElementById("loader");
  if (loader) {
    window.addEventListener("load", () => {
      gsap.to(loader, {
        opacity: 0,
        duration: 0.6,
        ease: "power2.inOut",
        onComplete: () => loader.remove(),
      });
    });
  }

  // -------------------------------
  // 2️⃣ Animación inicial del main
  // -------------------------------
  if (document.getElementById("page")) {
    gsap.fromTo(
      "#page",
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.9, ease: "power2.out" }
    );
  }

  // -------------------------------
  // 3️⃣ ScrollReveal animaciones
  // -------------------------------
  if (window.ScrollReveal) {
    const sr = ScrollReveal({
      duration: 900,
      distance: "50px",
      easing: "ease-out",
      reset: false,
    });

    sr.reveal(".fade-up", { origin: "bottom", delay: 200 });
    sr.reveal(".fade-left", { origin: "left", delay: 300 });
    sr.reveal(".fade-right", { origin: "right", delay: 300 });
  }

  // -------------------------------
  // 4️⃣ Smooth scroll mejorado
  // -------------------------------
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const target = document.querySelector(anchor.getAttribute("href"));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // -------------------------------
  // 5️⃣ Dark mode toggle automático
  // -------------------------------
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
  document.documentElement.classList.toggle("dark", prefersDark.matches);
  prefersDark.addEventListener("change", (e) => {
    document.documentElement.classList.toggle("dark", e.matches);
  });

  // -------------------------------
  // 6️⃣ Alert dinámico global
  // -------------------------------
  window.showAlert = (msg, type = "success") => {
    const alert = document.createElement("div");
    alert.className = `fixed top-5 right-5 px-4 py-2 rounded-lg shadow-lg z-[9999] ${
      type === "error" ? "bg-red-600" : "bg-green-600"
    } text-white font-semibold`;
    alert.textContent = msg;
    document.body.appendChild(alert);

    gsap.fromTo(alert, { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.4 });
    setTimeout(() => {
      gsap.to(alert, {
        opacity: 0,
        y: -20,
        duration: 0.5,
        onComplete: () => alert.remove(),
      });
    }, 4000);
  };

  // -------------------------------
  // 7️⃣ Typewriter efecto en títulos
  // -------------------------------
  document.querySelectorAll(".typewriter").forEach((el) => {
    const text = el.textContent.trim();
    el.textContent = "";
    let i = 0;
    const speed = 70;

    (function typing() {
      if (i < text.length) {
        el.textContent += text.charAt(i);
        i++;
        setTimeout(typing, speed);
      }
    })();
  });

  // -------------------------------
  // 8️⃣ Contadores animados avanzados
  // -------------------------------
  const counters = document.querySelectorAll(".counter");
  const animateCounter = (el) => {
    const target = parseInt(el.dataset.target || "0", 10);
    if (isNaN(target)) return;
    const duration = 1500;

    const step = (timestamp, startTime) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      el.textContent = Math.floor(progress * target).toLocaleString();
      if (progress < 1) requestAnimationFrame((t) => step(t, startTime));
    };

    requestAnimationFrame(step);
  };

  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.6 }
  );

  counters.forEach((c) => counterObserver.observe(c));

  // -------------------------------
  // 9️⃣ Parallax suave en secciones
  // -------------------------------
  const parallaxElems = document.querySelectorAll(".parallax");
  if (parallaxElems.length > 0) {
    window.addEventListener("scroll", () => {
      const scrollY = window.scrollY;
      parallaxElems.forEach((el) => {
        const speed = parseFloat(el.dataset.speed || "0.2");
        el.style.transform = `translateY(${scrollY * speed}px)`;
      });
    });
  }

  // -------------------------------
  // 🔟 Hover glow dinámico en botones
  // -------------------------------
  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("mouseenter", () => {
      gsap.to(btn, {
        boxShadow: "0px 0px 20px rgba(236,72,153,0.6)",
        scale: 1.05,
        duration: 0.3,
      });
    });
    btn.addEventListener("mouseleave", () => {
      gsap.to(btn, {
        boxShadow: "0px 0px 0px rgba(0,0,0,0)",
        scale: 1,
        duration: 0.3,
      });
    });
  });

  // -------------------------------
  // 1️⃣1️⃣ Scroll progress bar superior
  // -------------------------------
  const progressBar = document.createElement("div");
  Object.assign(progressBar.style, {
    position: "fixed",
    top: "0",
    left: "0",
    height: "4px",
    background: "linear-gradient(90deg, #ec4899, #a855f7)",
    width: "0%",
    zIndex: "9999",
    transition: "width 0.2s ease-out",
  });
  progressBar.id = "scroll-progress";
  document.body.appendChild(progressBar);

  window.addEventListener("scroll", () => {
    const scrollTop = window.scrollY;
    const docHeight = document.body.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    progressBar.style.width = `${progress}%`;
  });

  console.log("✅ base.js PRO optimizado y sin errores cargado 🚀");
});
