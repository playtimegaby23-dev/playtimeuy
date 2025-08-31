import { db } from "../firebase-config";
import { collection, addDoc, serverTimestamp } from "firebase/firestore";

/**
 * Registra una venta en Firestore con comisiones
 * @param {string} promotorId - ID del promotor que generó la venta
 * @param {number} precioFinal - Precio total que paga el cliente
 */
export const registrarVenta = async (promotorId, precioFinal) => {
  const precioBase = 750; // tu comisión fija
  const comisionPromotor = precioFinal - precioBase;

  try {
    const docRef = await addDoc(collection(db, "ventas"), {
      promotorId,
      precioFinal,
      precioBase,
      comisionPromotor,
      estado: "pendiente", // hasta que MP notifique
      fecha: serverTimestamp(),
    });

    return { success: true, id: docRef.id };
  } catch (error) {
    console.error("❌ Error al registrar venta:", error);
    return { success: false, error };
  }
};
