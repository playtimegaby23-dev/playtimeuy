// Base.js - Funcionalidades globales PlayTimeUY

document.addEventListener("DOMContentLoaded", () => {
  // Loader Fade Out
  const loader = document.getElementById("loader");
  if (loader) {
    setTimeout(() => {
      loader.classList.add("opacity-0", "transition-opacity", "duration-700");
      setTimeout(() => loader.remove(), 700);
    }, 1200);
  }

  // Navbar Scroll Effect
  const navbar = document.querySelector("nav");
  if (navbar) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 50) {
        navbar.classList.add("bg-dark", "shadow-lg");
      } else {
        navbar.classList.remove("bg-dark", "shadow-lg");
      }
    });
  }

  // Smooth Scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute("href")).scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    });
  });

  // Animar elementos en scroll
  const animatedElements = document.querySelectorAll(".animate-on-scroll");
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("animate__fadeInUp");
        entry.target.classList.remove("opacity-0");
      }
    });
  }, { threshold: 0.2 });

  animatedElements.forEach(el => {
    el.classList.add("opacity-0", "animate__animated");
    observer.observe(el);
  });
});
