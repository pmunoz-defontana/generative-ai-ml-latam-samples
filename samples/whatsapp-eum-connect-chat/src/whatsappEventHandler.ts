// Maneja eventos entrantes de WhatsApp y los envía a Amazon Connect
import { ConnectionsService } from "./services/connectionsService";
import { ChatService } from "./services/chatService";

const connections = new ConnectionsService();
const chat = new ChatService();

export async function handler(event: any): Promise<void> {
  const records = event.Records || [];
  for (const record of records) {
    const payload = JSON.parse(record.Sns?.Message || "{}");
    const text = payload.message?.text?.body || "";
    const phone = payload.metadata?.phone_number || "";
    const systemNumber = payload.metadata?.system_number || "";

    const existing = await connections.getContact(phone);
    let connectionToken = existing?.connectionToken;

    if (!connectionToken) {
      // No existe contacto, se inicia uno nuevo
      const resp = await chat.startChatAndStream(text, phone, "Whatsapp", payload.message?.customer_name || "NN", systemNumber);
      await connections.insertContact(phone, "Whatsapp", resp.contactId, resp.participantToken, resp.connectionToken, payload.message?.customer_name || "NN", systemNumber);
      connectionToken = resp.connectionToken;
    } else {
      // Existe contacto, se envía el mensaje
      await chat.sendMessage(text, connectionToken);
    }
  }
}
