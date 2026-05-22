import { InMemoryQueue } from "./queue";
import { NotificationRepo } from "../repositories/notificationRepo";
import { EmailProvider, SmsProvider, PushProvider } from "./providers";
import { logger } from "../logger";

export interface Providers {
  email: EmailProvider;
  sms: SmsProvider;
  push: PushProvider;
}

export class Dispatcher {
  private timer: NodeJS.Timeout | null = null;

  constructor(
    private queue: InMemoryQueue,
    private repo: NotificationRepo,
    private providers: Providers,
  ) {}

  start(intervalMs = 100): void {
    if (this.timer) return;
    this.timer = setInterval(() => void this.drain(), intervalMs);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  async drain(): Promise<void> {
    while (this.queue.size() > 0) {
      const n = this.queue.dequeue();
      if (!n) break;
      try {
        let result;
        if (n.channel === "email") {
          result = await this.providers.email.send(n.to, n.rendered, deriveSubject(n.template));
        } else if (n.channel === "sms") {
          result = await this.providers.sms.send(n.to, n.rendered);
        } else {
          result = await this.providers.push.send(n.to, n.rendered);
        }
        n.status = "sent";
        n.providerMessageId = result.providerMessageId;
        n.sentAt = new Date().toISOString();
      } catch (err) {
        n.status = "failed";
        n.error = (err as Error).message;
        logger.warn({ id: n.id, err: n.error }, "dispatch failed");
      }
      this.repo.save(n);
    }
  }
}

function deriveSubject(template: string): string {
  switch (template) {
    case "welcome":
      return "Welcome to FinsPoly";
    case "password_reset":
      return "Your password reset code";
    case "txn_alert":
      return "Transaction alert";
    case "statement_ready":
      return "Your statement is ready";
    default:
      return "Notification";
  }
}
