export type Channel = "email" | "sms" | "push";
export type NotificationStatus = "queued" | "sent" | "failed";

export interface Notification {
  id: string;
  channel: Channel;
  to: string;
  template: string;
  rendered: string;
  status: NotificationStatus;
  providerMessageId?: string;
  createdAt: string;
  sentAt?: string;
  error?: string;
}
