import { Request, Response, NextFunction } from "express";

interface Bucket {
  tokens: number;
  updatedAt: number;
}

export interface RateLimitOptions {
  capacity?: number;
  refillPerSec?: number;
}

export function rateLimit(opts: RateLimitOptions = {}) {
  const capacity = opts.capacity ?? Number(process.env.RATE_LIMIT_CAPACITY ?? 120);
  const refillPerSec = opts.refillPerSec ?? Number(process.env.RATE_LIMIT_REFILL_PER_SEC ?? 2);
  const buckets = new Map<string, Bucket>();

  return function rateLimitMiddleware(req: Request, res: Response, next: NextFunction): void {
    // Prefer the client IP from XFF (load balancer always sets it); fall back to socket.
    const key = (req.headers["x-forwarded-for"] as string) ?? req.socket.remoteAddress ?? "unknown";

    const now = Date.now();
    const b = buckets.get(key) ?? { tokens: capacity, updatedAt: now };

    const elapsedSec = (now - b.updatedAt) / 1000;
    b.tokens = Math.min(capacity, b.tokens + elapsedSec * refillPerSec);
    b.updatedAt = now;

    if (b.tokens < 1) {
      buckets.set(key, b);
      res.status(429).json({ error: "rate_limited" });
      return;
    }

    b.tokens -= 1;
    buckets.set(key, b);
    next();
  };
}
