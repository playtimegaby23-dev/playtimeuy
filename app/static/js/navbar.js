// ============================
// Navbar Interactions & Effects
// ============================

document.addEventListener("DOMContentLoaded", () => {
    const btnMobileMenu = document.getElementById("btn-mobile-menu");
    const mobileMenu = document.getElementById("mobile-menu");
    const navbar = document.querySelector("nav");
    const navLinks = document.querySelectorAll("nav a");

    // =========================
    // Toggle menú móvil
    // =========================
    if (btnMobileMenu && mobileMenu) {
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

        // Cerrar menú móvil al hacer clic en un link
        mobileMenu.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                mobileMenu.classList.add("hidden");
                btnMobileMenu.setAttribute("aria-expanded", false);
            });
        });
    }

    // =========================
    // Efecto scroll en navbar
    // =========================
    let lastScrollTop = 0;
    window.addEventListener("scroll", () => {
        const currentScroll = window.scrollY;

        if (currentScroll > 10) {
            navbar.classList.add("bg-gray-900/95", "shadow-lg", "backdrop-blur-md");
        } else {
            navbar.classList.remove("bg-gray-900/95", "shadow-lg", "backdrop-blur-md");
        }

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
    navLinks.forEach(link => {
        link.addEventListener("mouseenter", () => {
            link.style.transition = "all 0.25s ease";
            link.style.textShadow = "0px 0px 6px rgba(236,72,153,0.7)";
        });

        link.addEventListener("mouseleave", () => {
            link.style.textShadow = "none";
        });
    });

    // =========================
    // Resaltar link activo
    // =========================
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        // Ajustar rutas nuevas
        const href = link.getAttribute("href");
        if (
            (currentPath.includes("/home/") && href.includes("home")) ||
            (currentPath.includes("/user/") && href.includes("profile")) ||
            (currentPath.includes("/auth/") && (href.includes("login") || href.includes("register"))) ||
            currentPath === href
        ) {
            link.classList.add("text-pink-500", "font-semibold");
        } else {
            link.classList.remove("text-pink-500", "font-semibold");
        }
    });
});

// ============================
// Animación fadeIn personalizada
// ============================
const style = document.createElement("style");
style.innerHTML = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
`;
document.head.appendChild(style);
