// ============================
// Navbar Interactions & Effects
// ============================

document.addEventListener("DOMContentLoaded", () => {
    const btnMobileMenu = document.getElementById("btn-mobile-menu");
    const mobileMenu = document.getElementById("mobile-menu");

    if (btnMobileMenu && mobileMenu) {
        // Toggle menú móvil con animación
        btnMobileMenu.addEventListener("click", () => {
            const expanded = btnMobileMenu.getAttribute("aria-expanded") === "true";
            btnMobileMenu.setAttribute("aria-expanded", !expanded);

            mobileMenu.classList.toggle("hidden");

            if (!expanded) {
                mobileMenu.classList.add("animate-fadeIn");
                setTimeout(() => {
                    mobileMenu.classList.remove("animate-fadeIn");
                }, 300);
            }
        });
    }

    // =========================
    // Efecto scroll en navbar
    // =========================
    const navbar = document.querySelector("nav");
    let lastScrollTop = 0;

    window.addEventListener("scroll", () => {
        let currentScroll = window.scrollY;

        // Cambiar opacidad y sombra al hacer scroll
        if (currentScroll > 10) {
            navbar.classList.add("bg-gray-900/95", "shadow-lg", "backdrop-blur-md");
        } else {
            navbar.classList.remove("bg-gray-900/95", "shadow-lg", "backdrop-blur-md");
        }

        // Auto-ocultar en scroll hacia abajo y mostrar en scroll hacia arriba
        if (currentScroll > lastScrollTop && currentScroll > 100) {
            navbar.style.transform = "translateY(-100%)";
        } else {
            navbar.style.transform = "translateY(0)";
        }
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    });

    // =========================
    // Hover dinámico en links
    // =========================
    const navLinks = document.querySelectorAll("nav a");

    navLinks.forEach(link => {
        link.addEventListener("mouseenter", () => {
            link.style.transition = "all 0.25s ease";
            link.style.textShadow = "0px 0px 6px rgba(236,72,153,0.7)";
        });

        link.addEventListener("mouseleave", () => {
            link.style.textShadow = "none";
        });
    });
});
