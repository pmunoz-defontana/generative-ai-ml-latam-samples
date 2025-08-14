// Servicio para administrar conexiones en DynamoDB
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, UpdateCommand, QueryCommand, DeleteCommand } from "@aws-sdk/lib-dynamodb";

const TABLE_NAME = process.env.TABLE_NAME || "";

function buildUpdateExpression(data: Record<string, any>) {
  const names: Record<string, string> = {};
  const values: Record<string, any> = {};
  const parts: string[] = [];
  let i = 0;
  for (const [key, val] of Object.entries(data)) {
    const name = `#n${i}`;
    const value = `:v${i}`;
    names[name] = key;
    values[value] = val;
    parts.push(`${name} = ${value}`);
    i++;
  }
  return {
    ExpressionAttributeNames: names,
    ExpressionAttributeValues: values,
    UpdateExpression: `SET ${parts.join(", ")}`,
  };
}

export class ConnectionsService {
  private client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

  // Inserta un contacto nuevo
  async insertContact(customerId: string, channel: string, contactId: string, participantToken: string, connectionToken: string, name: string, systemNumber: string) {
    const expr = buildUpdateExpression({ customerId, participantToken, connectionToken, name, channel, systemNumber });
    await this.client.send(new UpdateCommand({
      TableName: TABLE_NAME,
      Key: { contactId },
      ...expr,
      ReturnValues: "ALL_NEW",
    }));
  }

  // Actualiza un contacto existente
  async updateContact(customerId: string, channel: string, contactId: string, participantToken: string, connectionToken: string, name: string, systemNumber: string) {
    const expr = buildUpdateExpression({ customerId, participantToken, connectionToken, name, channel, systemNumber });
    await this.client.send(new UpdateCommand({
      TableName: TABLE_NAME,
      Key: { contactId },
      ...expr,
      ReturnValues: "UPDATED_NEW",
    }));
  }

  // Obtiene un contacto por customerId
  async getContact(customerId: string, indexName = "customerId-index") {
    const result = await this.client.send(new QueryCommand({
      TableName: TABLE_NAME,
      IndexName: indexName,
      KeyConditionExpression: "#cid = :cid",
      ExpressionAttributeNames: { "#cid": "customerId" },
      ExpressionAttributeValues: { ":cid": customerId },
    }));
    return result.Items?.[0];
  }

  // Elimina un contacto por contactId
  async removeContactId(contactId: string) {
    await this.client.send(new DeleteCommand({ TableName: TABLE_NAME, Key: { contactId } }));
  }

  // Obtiene el token de conexión
  async getConnectionToken(contactId: string) {
    const result = await this.client.send(new QueryCommand({
      TableName: TABLE_NAME,
      KeyConditionExpression: "#id = :id",
      ExpressionAttributeNames: { "#id": "contactId" },
      ExpressionAttributeValues: { ":id": contactId },
    }));
    return result.Items?.[0]?.connectionToken;
  }

  // Obtiene el objeto del cliente
  async getCustomer(contactId: string) {
    const result = await this.client.send(new QueryCommand({
      TableName: TABLE_NAME,
      KeyConditionExpression: "#id = :id",
      ExpressionAttributeNames: { "#id": "contactId" },
      ExpressionAttributeValues: { ":id": contactId },
    }));
    return result.Items?.[0];
  }
}
