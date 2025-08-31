/* =============================
 PlayTimeUY – Interacciones v2 (mejorado)
 ============================= */

// 🔹 Helpers
const qs  = (sel, ctx = document) => ctx.querySelector(sel);
const qsa = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

// =============================
// Reveal on scroll (IntersectionObserver)
// =============================
(function setupFadeEffects(){
  if (!("IntersectionObserver" in window)) return;

  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("opacity-100", "translate-y-0");
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });

  qsa(".fade-up, .fade-in").forEach(el => {
    if (el.classList.contains("fade-up")) {
      el.classList.add("opacity-0","translate-y-4","transition","duration-700","ease-out");
      el.style.willChange = "opacity, transform";
    } else {
      el.classList.add("opacity-0","transition","duration-700","ease-out");
      el.style.willChange = "opacity";
    }
    io.observe(el);
  });
})();

// =============================
// Glow dinámico en cards (mousemove)
// =============================
document.addEventListener("pointermove", (e) => {
  qsa(".card-pro").forEach(card => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    card.style.setProperty("--mx", `${x}%`);
  });
}, { passive: true });

// =============================
// Efecto ripple minimal en botones
// =============================
function setupRipple(btn){
  if (!btn) return;
  btn.style.position ||= "relative";
  btn.style.overflow = "hidden";

  btn.addEventListener("click", (e) => {
    const r = document.createElement("span");
    const rect = btn.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    r.style.cssText = `
      position:absolute; inset:0; pointer-events:none;
      background: radial-gradient(circle at ${x}% ${y}%, rgba(255,255,255,0.35), transparent 40%);
      transition: opacity .6s ease;
    `;
    btn.appendChild(r);

    requestAnimationFrame(() => { r.style.opacity = "0"; });
    setTimeout(() => r.remove(), 650);
  });
}
document.addEventListener("DOMContentLoaded", () => {
  qsa(".btn-primary, .btn-secondary, .btn-ghost").forEach(setupRipple);
});

// =============================
// Scroll suave desde el indicador
// =============================
qs(".scroll-indicator")?.addEventListener("click", () => {
  window.scrollTo({ top: window.innerHeight, behavior: "smooth" });
}, { once: true });

// =============================
// Autoplay seguro (prefers-reduced-motion)
// =============================
(function safeAutoplay(){
  try {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const vid = qs("section[role='banner'] video");
    if (prefersReduced && vid) {
      vid.removeAttribute("autoplay");
      vid.pause?.();
    }
  } catch(e){ console.warn("🎬 Autoplay control error:", e); }
})();

// =============================
// Carrusel: controles + drag
// =============================
(function setupCarousel(){
  const track = qs(".carousel-track");
  if (!track) return;

  const prev = qs(".carousel-btn.prev");
  const next = qs(".carousel-btn.next");
  const card = () => track.querySelector(".carousel-card");
  const gap  = 16;

  const scrollByCards = (dir = 1) => {
    const c = card();
    const width = c ? c.getBoundingClientRect().width + gap : 300;
    track.scrollBy({ left: dir * width, behavior: "smooth" });
  };

  prev?.addEventListener("click", () => scrollByCards(-1));
  next?.addEventListener("click", () => scrollByCards(1));

  let isDown = false, startX = 0, scrollLeft = 0;
  track.addEventListener("pointerdown", (e) => {
    isDown = true;
    track.setPointerCapture(e.pointerId);
    startX = e.clientX;
    scrollLeft = track.scrollLeft;
    track.classList.add("dragging");
  });
  track.addEventListener("pointermove", (e) => {
    if (!isDown) return;
    const dx = e.clientX - startX;
    track.scrollLeft = scrollLeft - dx;
  });
  ["pointerup","pointercancel","pointerleave"].forEach(evt => {
    track.addEventListener(evt, () => {
      isDown = false;
      track.classList.remove("dragging");
    });
  });
})();

// =============================
// Validaciones globales
// =============================
function validateEmail(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }
function validateNotEmpty(v){ return (v ?? "").trim().length > 0; }

window.ptuy = { validateEmail, validateNotEmpty };
