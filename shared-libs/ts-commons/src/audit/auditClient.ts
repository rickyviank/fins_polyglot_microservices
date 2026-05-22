import { randomUUID } from "node:crypto";

export interface AuditEvent {
  event_id: string;
  occurred_at: string;
  service: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  outcome: "success" | "failure" | "denied";
  metadata?: Record<string, unknown>;
}

export interface AuditClientOptions {
  auditServiceUrl: string;
  service: string;
  timeoutMs?: number;
}

export class AuditClient {
  private readonly url: string;
  private readonly service: string;
  private readonly timeoutMs: number;

  constructor(opts: AuditClientOptions) {
    this.url = opts.auditServiceUrl.replace(/\/$/, "");
    this.service = opts.service;
    this.timeoutMs = opts.timeoutMs ?? 500;
  }

  async emit(
    actor: string,
    action: string,
    resourceType: string,
    resourceId: string,
    outcome: AuditEvent["outcome"],
    metadata?: Record<string, unknown>,
  ): Promise<void> {
    const event: AuditEvent = {
      event_id: randomUUID(),
      occurred_at: new Date().toISOString(),
      service: this.service,
      actor,
      action,
      resource_type: resourceType,
      resource_id: resourceId,
      outcome,
      metadata,
    };

    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), this.timeoutMs);
    try {
      await fetch(`${this.url}/v1/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event),
        signal: ctl.signal,
      });
    } catch (err) {
      // best-effort; never throw out of audit emission
      // eslint-disable-next-line no-console
      console.warn(`[audit] emit failed action=${action} res=${resourceType}/${resourceId}: ${(err as Error).message}`);
    } finally {
      clearTimeout(timer);
    }
  }
}
