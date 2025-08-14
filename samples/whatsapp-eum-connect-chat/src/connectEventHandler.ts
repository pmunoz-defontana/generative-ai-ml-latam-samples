// Procesa eventos desde Amazon Connect y responde por WhatsApp
import { ConnectionsService } from "./services/connectionsService";
import { sendWhatsAppText, sendWhatsAppAttachment } from "./services/whatsappService";

const connections = new ConnectionsService();

export async function handler(event: any): Promise<void> {
  const records = event.Records || [];
  for (const record of records) {
    const sns = record.Sns || {};
    const message = JSON.parse(sns.Message || "{}");
    const type = message.Type;
    const role = message.ParticipantRole;
    if (role === "CUSTOMER") continue;

    if (type === "MESSAGE") {
      const customer = await connections.getCustomer(message.ContactId);
      if (customer) {
        await sendWhatsAppText(message.Content, customer.customerId, customer.systemNumber);
      }
    }

    if (type === "ATTACHMENT") {
      const customer = await connections.getCustomer(message.ContactId);
      if (customer) {
        for (const att of message.Attachments || []) {
          if (att.Status === "APPROVED") {
            // TODO: obtener URL firmada del adjunto
            await sendWhatsAppAttachment(att.Url || "", att.ContentType || "", att.AttachmentName || "", customer.customerId, customer.systemNumber);
          }
        }
      }
    }

    if (type === "EVENT") {
      // Eventos de sistema como cierre de chat
      if (message.ContentType === "application/vnd.amazonaws.connect.event.chat.ended") {
        await connections.removeContactId(message.InitialContactId);
      }
    }
  }
}
