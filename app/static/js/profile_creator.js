// profile_creator.js — Funcionalidades exclusivas para el perfil de Creadora en PlayTimeUY

// Espera a que el DOM cargue completamente
document.addEventListener("DOMContentLoaded", () => {
  console.log("🔧 Perfil de Creadora cargado");

  // ---------------------------
  // 🏷️ Manejo de precios dinámicos y promociones
  // ---------------------------
  const priceInput = document.getElementById("subscription-price");
  const promoCheckbox = document.getElementById("promo-active");
  const promoInput = document.getElementById("promo-percentage");
  const pricePreview = document.getElementById("price-preview");

  function updatePricePreview() {
    const basePrice = parseFloat(priceInput.value) || 0;
    const promoActive = promoCheckbox?.checked;
    const discount = promoActive ? parseFloat(promoInput.value) || 0 : 0;
    const finalPrice = basePrice * (1 - discount / 100);
    pricePreview.textContent = `$${finalPrice.toFixed(2)}`;
  }

  [priceInput, promoCheckbox, promoInput].forEach((el) => {
    if (el) el.addEventListener("input", updatePricePreview);
  });

  updatePricePreview();

  // ---------------------------
  // 💸 Selección de métodos de cobro
  // ---------------------------
  const paymentSelect = document.getElementById("payment-methods");
  const walletDisplay = document.getElementById("wallet-display");

  if (paymentSelect && walletDisplay) {
    paymentSelect.addEventListener("change", () => {
      const selected = paymentSelect.value;
      walletDisplay.textContent = `Método seleccionado: ${selected}`;
    });
  }

  // ---------------------------
  // 📅 Calendario de disponibilidad para sexting
  // ---------------------------
  const calendar = document.getElementById("availability-calendar");
  const chatRate = document.getElementById("chat-rate");

  if (calendar && chatRate) {
    calendar.addEventListener("change", () => {
      console.log("Disponibilidad actualizada:", calendar.value);
    });

    chatRate.addEventListener("input", () => {
      console.log(`Precio por sesión de sexting: $${chatRate.value}`);
    });
  }

  // ---------------------------
  // 🔗 Sincronización con grupos de Telegram
  // ---------------------------
  const telegramBtn = document.getElementById("import-telegram");

  if (telegramBtn) {
    telegramBtn.addEventListener("click", async () => {
      try {
        const groupURL = prompt("Pegá el link del grupo/canal de Telegram:");
        if (groupURL && groupURL.startsWith("https://t.me/")) {
          // Aquí podrías enviar a backend para validarlo y guardarlo
          console.log("Grupo importado:", groupURL);
          alert("Grupo de Telegram importado correctamente ✅");
        } else {
          alert("El link no parece válido. Asegúrate que empiece por https://t.me/");
        }
      } catch (error) {
        console.error("Error al importar grupo de Telegram:", error);
        alert("Ocurrió un error al importar el grupo");
      }
    });
  }

  // ---------------------------
  // ⏱️ Control de duración y disponibilidad para chats
  // ---------------------------
  const sextingDuration = document.getElementById("sexting-duration");
  const timePreview = document.getElementById("sexting-time-preview");

  if (sextingDuration && timePreview) {
    sextingDuration.addEventListener("input", () => {
      timePreview.textContent = `${sextingDuration.value} minutos disponibles`;
    });
  }

  // ---------------------------
  // 📥 Guardar configuración con botón
  // ---------------------------
  const saveConfigBtn = document.getElementById("save-config-btn");

  if (saveConfigBtn) {
    saveConfigBtn.addEventListener("click", () => {
      const config = {
        price: parseFloat(priceInput.value),
        promo: promoCheckbox?.checked ? parseFloat(promoInput.value) : 0,
        paymentMethod: paymentSelect?.value,
        availability: calendar?.value,
        sextingRate: chatRate?.value,
        sextingDuration: sextingDuration?.value,
      };

      console.log("Configuración guardada:", config);
      alert("✅ Tu configuración fue guardada correctamente.");
    });
  }
});
