/* =============================
PlayTimeUY – Interacciones
============================= */

// Reveal on scroll (IntersectionObserver)
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) e.target.classList.add('opacity-100','translate-y-0');
  });
}, { threshold: 0.2 });

document.querySelectorAll('.fade-up').forEach(el => {
  el.classList.add('opacity-0','translate-y-4','transition','duration-700','will-change-transform');
  io.observe(el);
});
document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

// Glow dinámico en cards (sigue el mouse)
document.querySelectorAll('.card-pro').forEach(card => {
  card.addEventListener('pointermove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    card.style.setProperty('--mx', x + '%');
  });
});

// Efecto ripple minimal en botones
function addRipple(btn){
  btn.addEventListener('click', (e)=>{
    const r = document.createElement('span');
    r.style.position='absolute';
    r.style.inset='0';
    r.style.background='radial-gradient(circle at var(--x,50%) var(--y,50%), rgba(255,255,255,0.35), transparent 40%)';
    const rect = btn.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    r.style.setProperty('--x', x+'%');
    r.style.setProperty('--y', y+'%');
    r.style.pointerEvents='none';
    r.style.transition='opacity .6s ease';
    btn.appendChild(r);
    requestAnimationFrame(()=>{ r.style.opacity='0'; });
    setTimeout(()=> r.remove(), 650);
  });
}
document.querySelectorAll('.btn-primary, .btn-secondary, .btn-ghost').forEach(addRipple);

// Scroll suave desde el indicador
const indicator = document.querySelector('.scroll-indicator');
if (indicator) {
  indicator.addEventListener('click', () => {
    window.scrollTo({ top: window.innerHeight, behavior: 'smooth' });
  });
}

// Autoplay seguro si usuario prefiere menos movimiento
try {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const vid = document.querySelector('section[role="banner"] video');
  if (prefersReduced && vid) { vid.removeAttribute('autoplay'); vid.pause?.(); }
} catch {}

// Carrusel: controles prev/next + drag con scroll
(function setupCarousel(){
  const track = document.querySelector('.carousel-track');
  if (!track) return;
  const prev = document.querySelector('.carousel-btn.prev');
  const next = document.querySelector('.carousel-btn.next');
  const card = () => track.querySelector('.carousel-card');
  const gap = 16;

  function scrollByCards(dir = 1){
    const c = card();
    const width = c ? c.getBoundingClientRect().width + gap : 300;
    track.scrollBy({ left: dir * width, behavior: 'smooth' });
  }
  prev?.addEventListener('click', () => scrollByCards(-1));
  next?.addEventListener('click', () => scrollByCards(1));

  let isDown = false, startX = 0, scrollLeft = 0;
  track.addEventListener('pointerdown', (e) => {
    isDown = true; track.setPointerCapture(e.pointerId);
    startX = e.clientX; scrollLeft = track.scrollLeft;
  });
  track.addEventListener('pointermove', (e) => {
    if (!isDown) return;
    const dx = e.clientX - startX;
    track.scrollLeft = scrollLeft - dx;
  });
  ['pointerup','pointercancel','pointerleave'].forEach(evt => {
    track.addEventListener(evt, () => { isDown = false; });
  });
})();

// Validaciones simples disponibles globalmente
function validateEmail(v){ return /.+@.+\..+/.test(v); }
function validateNotEmpty(v){ return (v ?? '').trim().length > 0; }
window.ptuy = { validateEmail, validateNotEmpty };
