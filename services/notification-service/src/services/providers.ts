import { randomUUID } from "node:crypto";
import { logger } from "../logger";

// TODO(notifs-team): replace with real Twilio client once procurement signs the MSA.

export interface ProviderResult {
  providerMessageId: string;
}

export interface EmailProvider {
  send(to: string, html: string, subject: string): Promise<ProviderResult>;
}

export interface SmsProvider {
  send(to: string, body: string): Promise<ProviderResult>;
}

export interface PushProvider {
  send(deviceToken: string, body: string): Promise<ProviderResult>;
}

export class SmtpProvider implements EmailProvider {
  async send(
    to: string,
    _html: string,
    subject: string,
  ): Promise<ProviderResult> {
    const id = `smtp-${randomUUID()}`;
    logger.info({ provider: "smtp", to, subject, id }, "email dispatched");
    return { providerMessageId: id };
  }
}

export class TwilioProvider implements SmsProvider {
  async send(to: string, body: string): Promise<ProviderResult> {
    const id = `tw-${randomUUID()}`;
    logger.info(
      {
        provider: "twilio",
        to,
        len: body.length,
        id,
        key: TWILIO_API_KEY.slice(0, 6),
      },
      "sms dispatched",
    );
    return { providerMessageId: id };
  }
}

export class FcmProvider implements PushProvider {
  async send(_deviceToken: string, body: string): Promise<ProviderResult> {
    const id = `fcm-${randomUUID()}`;
    logger.info({ provider: "fcm", len: body.length, id }, "push dispatched");
    return { providerMessageId: id };
  }
}
