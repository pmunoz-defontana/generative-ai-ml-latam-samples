// Servicio para interactuar con Amazon Connect Chat
import { ConnectClient, StartChatContactCommand, StartContactStreamingCommand } from "@aws-sdk/client-connect";
import { ConnectParticipantClient, SendMessageCommand, CreateParticipantConnectionCommand } from "@aws-sdk/client-connectparticipant";

const INSTANCE_ID = process.env.INSTANCE_ID || "";
const CONTACT_FLOW_ID = process.env.CONTACT_FLOW_ID || "";
const CHAT_DURATION_MINUTES = parseInt(process.env.CHAT_DURATION_MINUTES || "60");
const TOPIC_ARN = process.env.TOPIC_ARN;

export class ChatService {
  private connect = new ConnectClient({});
  private participant = new ConnectParticipantClient({});

  // Inicia un chat nuevo
  async startChat(message: string, phone: string, channel: string, name = "unknown", systemNumber = "unknown") {
    return await this.connect.send(new StartChatContactCommand({
      InstanceId: INSTANCE_ID,
      ContactFlowId: CONTACT_FLOW_ID,
      Attributes: {
        Channel: channel,
        customerId: phone,
        customerName: name,
        systemNumber,
      },
      ParticipantDetails: { DisplayName: name },
      InitialMessage: { ContentType: "text/plain", Content: message },
      ChatDurationInMinutes: CHAT_DURATION_MINUTES,
      SupportedMessagingContentTypes: [
        "text/plain",
        "text/markdown",
        "application/json",
        "application/vnd.amazonaws.connect.message.interactive",
        "application/vnd.amazonaws.connect.message.interactive.response",
      ],
    }));
  }

  // Envia un mensaje al chat
  async sendMessage(content: string, connectionToken: string) {
    try {
      await this.participant.send(new SendMessageCommand({
        ContentType: "text/plain",
        Content: content,
        ConnectionToken: connectionToken,
      }));
      return null;
    } catch (err: any) {
      if (err.name === "AccessDeniedException") return "ACCESS_DENIED";
      if (err.name === "ThrottlingException") return "THROTTLING";
      if (err.name === "ValidationException") return "VALIDATION_ERROR";
      return "UNEXPECTED_ERROR";
    }
  }

  // Inicia el streaming de un chat
  async startStream(contactId: string) {
    if (!TOPIC_ARN) return null;
    return await this.connect.send(new StartContactStreamingCommand({
      InstanceId: INSTANCE_ID,
      ContactId: contactId,
      ChatStreamingConfiguration: { StreamingEndpointArn: TOPIC_ARN },
    }));
  }

  // Crea una conexión de participante
  async createConnection(participantToken: string) {
    return await this.participant.send(new CreateParticipantConnectionCommand({
      Type: ["CONNECTION_CREDENTIALS"],
      ParticipantToken: participantToken,
      ConnectParticipant: true,
    }));
  }

  // Inicia chat y streaming
  async startChatAndStream(message: string, phone: string, channel: string, name = "unknown", systemNumber = "unknown") {
    const start = await this.startChat(message, phone, channel, name, systemNumber);
    const participantToken = start.ParticipantToken!;
    const contactId = start.ContactId!;
    await this.startStream(contactId);
    const conn = await this.createConnection(participantToken);
    const connectionToken = conn.ConnectionCredentials!.ConnectionToken!;
    return { contactId, participantToken, connectionToken };
  }

  // Envía un mensaje con reintento de conexión
  async sendMessageWithRetryConnection(text: string, message: any, connectionToken: string) {
    const result = await this.sendMessage(text, connectionToken);
    if (result === "ACCESS_DENIED") {
      return await this.startChatAndStream(text || "Nueva conversacion", message.phone_number, "Whatsapp", message.message?.customer_name ?? "NN", message.phone_number_id);
    }
    return { contactId: null, participantToken: null, connectionToken: null };
  }
}
