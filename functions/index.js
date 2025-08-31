const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");
const mercadopago = require("mercadopago");

admin.initializeApp();
const app = express();
app.use(cors({ origin: true }));
app.use(express.json());

// 🔹 Configuración MercadoPago
mercadopago.configure({
  access_token: "APP_USR-8983986661644091-081911-db4d3357b3a9cc4c1fc9d6c0f92839"
});

// ✅ Crear preferencia con referencia a la creadora
app.post("/crear-preferencia", async (req, res) => {
  try {
    const { titulo, precio, creadora_id } = req.body;

    const preference = {
      items: [
        {
          title: titulo || "Servicio PlayTimeUY",
          unit_price: Number(precio) || 750,
          quantity: 1,
        },
      ],
      back_urls: {
        success: "https://playtimeuy.web.app/success",
        failure: "https://playtimeuy.web.app/failure",
        pending: "https://playtimeuy.web.app/pending",
      },
      auto_return: "approved",
      external_reference: creadora_id || "empresa", // 🔹 Identifica a la creadora
      notification_url: "https://us-central1-playtimeuy.cloudfunctions.net/api/webhook"
    };

    const response = await mercadopago.preferences.create(preference);

    res.json({
      id: response.body.id,
      init_point: response.body.init_point,
    });

  } catch (error) {
    console.error("❌ Error al crear preferencia:", error);
    res.status(500).json({ error: "Error al crear preferencia" });
  }
});

// ✅ Webhook con comisiones
app.post("/webhook", async (req, res) => {
  try {
    console.log("📩 Webhook recibido:", req.body);

    // 🔹 Mercado Pago a veces manda solo IDs, hay que consultar el pago completo
    if (req.body.type === "payment") {
      const paymentId = req.body.data.id;

      const payment = await mercadopago.payment.findById(paymentId);
      const pagoData = payment.body;

      // Datos principales
      const monto = pagoData.transaction_amount;
      const estado = pagoData.status;
      const comprador = pagoData.payer?.email || "desconocido";
      const creadora_id = pagoData.external_reference || "empresa";

      // 🔹 Comisiones (ejemplo: 20% empresa / 80% creadora)
      const comision_empresa = monto * 0.20;
      const ganancia_creadora = monto * 0.80;

      // Guardar en Firestore
      await admin.firestore().collection("pagos").add({
        id_pago: paymentId,
        monto,
        estado,
        comprador,
        creadora_id,
        comision_empresa,
        ganancia_creadora,
        fecha: admin.firestore.FieldValue.serverTimestamp(),
      });

      console.log("✅ Pago guardado en Firestore:", paymentId);
    }

    res.sendStatus(200);
  } catch (error) {
    console.error("❌ Error en webhook:", error);
    res.sendStatus(500);
  }
});

exports.api = functions.https.onRequest(app);
