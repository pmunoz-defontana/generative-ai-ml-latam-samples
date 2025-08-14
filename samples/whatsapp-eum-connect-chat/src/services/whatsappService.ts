// Servicio para interactuar con WhatsApp a través de Social Messaging
// Nota: El cliente de Social Messaging es un marcador de posición
import { SNSClient, PublishCommand } from "@aws-sdk/client-sns";

const sns = new SNSClient({});

// Envía un mensaje de texto por WhatsApp
export async function sendWhatsAppText(message: string, phone: string, systemNumber: string) {
  await sns.send(new PublishCommand({
    Message: message,
    PhoneNumber: phone,
  }));
}

// Envía un adjunto por WhatsApp utilizando una URL firmada
export async function sendWhatsAppAttachment(url: string, contentType: string, filename: string, phone: string, systemNumber: string) {
  await sns.send(new PublishCommand({
    Message: url,
    PhoneNumber: phone,
    MessageAttributes: {
      'contentType': { DataType: 'String', StringValue: contentType },
      'filename': { DataType: 'String', StringValue: filename }
    }
  }));
}
