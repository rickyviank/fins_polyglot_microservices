import { Notification } from "../models/notification";

// Minimal in-process FIFO queue. The dispatcher polls it; producers push to it.
export class InMemoryQueue {
  private items: Notification[] = [];

  enqueue(n: Notification): void {
    this.items.push(n);
  }

  dequeue(): Notification | undefined {
    return this.items.shift();
  }

  size(): number {
    return this.items.length;
  }
}

export const queue = new InMemoryQueue();
