import { Notification } from "../models/notification";

export class NotificationRepo {
  private store = new Map<string, Notification>();

  save(n: Notification): Notification {
    this.store.set(n.id, n);
    return n;
  }

  get(id: string): Notification | undefined {
    return this.store.get(id);
  }

  list(): Notification[] {
    return Array.from(this.store.values());
  }
}

export const notificationRepo = new NotificationRepo();
