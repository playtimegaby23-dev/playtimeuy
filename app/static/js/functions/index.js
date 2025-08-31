/* Firebase Functions + Mercado Pago */
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");
const mercadopago = require("mercadopago");

admin.initializeApp();
const db = admin.firestore();

// ──────────────────────────────────────────────────────────────
// Config MP
const MP_ACCESS_TOKEN = functions.config().mp.token;
const MP_PUBLIC_KEY = functions.config().mp.pubkey;
const SITE_URL = functions.config().site.url || "http://localhost:5173";

mercadopago.configure({ access_token: MP_ACCESS_TOKEN });

// ──────────────────────────────────────────────────────────────
// App Express para endpoints HTTP
const app = express();
app.use(cors({ origin: true }));
app.use(express.json());

// Helpers
const PRECIO_BASE_EMPRESA = 750;

function assert(cond, msg) {
  if (!cond) {
    const e = new Error(msg);
    e.status = 400;
    throw e;
  }
}

// ──────────────────────────────────────────────────────────────
// 1) Crear preferencia
// Body esperado: { promotorId, precioFinal, compradorUid?, creadorId? }
app.post("/mp/create-preference", async (req, res) => {
  try {
    const { promotorId, precioFinal, compradorUid = null, creadorId = null } = req.body || {};

    assert(promotorId, "Falta promotorId");
    assert(typeof precioFinal === "number", "precioFinal debe ser numérico");
    assert(precioFinal >= PRECIO_BASE_EMPRESA, `precioFinal debe ser >= ${PRECIO_BASE_EMPRESA}`);

    const comisionPromotor = precioFinal - PRECIO_BASE_EMPRESA;

    // Creamos registro preliminar de la venta en Firestore (estado: pendiente)
    const ventaRef = await db.collection("ventas").add({
      promotorId,
      compradorUid,
      creadorId,
      precioFinal,
      precioBase: PRECIO_BASE_EMPRESA,
      comisionPromotor,
      estado: "pendiente",
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      mp: { preferenceId: null, paymentId: null },
    });

    // preference con metadata para rastrear
    const preference = {
      items: [
        {
          title: "Suscripción mensual PlayTimeUY",
          quantity: 1,
          unit_price: precioFinal,
          currency_id: "UYU",
        },
      ],
      back_urls: {
        success: `${SITE_URL}/pago/success?venta=${ventaRef.id}`,
        failure: `${SITE_URL}/pago/failure?venta=${ventaRef.id}`,
        pending: `${SITE_URL}/pago/pending?venta=${ventaRef.id}`,
      },
      auto_return: "approved",
      metadata: {
        promotorId,
        ventaId: ventaRef.id,
        precioFinal,
        precioBase: PRECIO_BASE_EMPRESA,
        comisionPromotor,
      },
      // útil si querés leerlo sin metadata
      external_reference: `venta_${ventaRef.id}_${promotorId}`,
      notification_url: `https://${
        process.env.GCLOUD_PROJECT
      }.cloudfunctions.net/api/mp/webhook`, // URL pública del webhook
    };

    const mpRes = await mercadopago.preferences.create(preference);

    await ventaRef.update({
      "mp.preferenceId": mpRes.body.id,
      init_point: mpRes.body.init_point,
      sandbox_init_point: mpRes.body.sandbox_init_point || null,
    });

    res.json({
      ok: true,
      preferenceId: mpRes.body.id,
      init_point: mpRes.body.init_point,
      publicKey: MP_PUBLIC_KEY, // el frontend lo usa para inicializar el SDK
      ventaId: ventaRef.id,
    });
  } catch (err) {
    console.error("create-preference error:", err);
    res.status(err.status || 500).json({ ok: false, error: err.message });
  }
});

// ──────────────────────────────────────────────────────────────
// 2) Webhook de Mercado Pago
app.post("/mp/webhook", async (req, res) => {
  try {
    const { type, data } = req.body || {};
    // Mercado Pago puede mandar "payment", "merchant_order", etc.
    if (type !== "payment") {
      return res.status(200).send("ignored");
    }

    const paymentId = data && data.id;
    if (!paymentId) return res.status(400).send("missing payment id");

    // Obtener pago completo
    const result = await mercadopago.payment.findById(paymentId);
    const p = result.body;

    // Metadatos que pusimos al crear la preferencia
    const meta = p.metadata || {};
    const ventaId = meta.ventaId;
    if (!ventaId) return res.status(200).send("no ventaId in metadata");

    // Actualizamos la venta
    const ventaRef = db.collection("ventas").doc(ventaId);
    const update = {
      "mp.paymentId": String(paymentId),
      "mp.status": p.status,
      "mp.status_detail": p.status_detail,
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    };

    if (p.status === "approved") {
      update.estado = "pagado";
      update.pagadoAt = admin.firestore.FieldValue.serverTimestamp();
    } else if (p.status === "rejected") {
      update.estado = "rechazado";
    } else {
      update.estado = p.status; // pending, in_process, etc.
    }

    await ventaRef.set(update, { merge: true });

    return res.status(200).send("ok");
  } catch (err) {
    console.error("webhook error:", err);
    return res.status(500).send("error");
  }
});

// ──────────────────────────────────────────────────────────────
// Export Express app como una sola Function
exports.api = functions.region("southamerica-east1").https.onRequest(app);
