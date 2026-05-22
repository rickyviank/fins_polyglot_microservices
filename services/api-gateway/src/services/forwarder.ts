import { Request, Response, NextFunction } from "express";
import { logger } from "../logger";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

export function buildForwarder(baseUrl: string) {
  return async function forward(req: Request, res: Response, next: NextFunction): Promise<void> {
    const target = `${baseUrl.replace(/\/$/, "")}${req.originalUrl}`;

    // Build outbound headers — passthrough everything the client sent, plus our
    // correlation ID so downstream logs can join.
    const headers: Record<string, string> = {};
    for (const [k, v] of Object.entries(req.headers)) {
      if (HOP_BY_HOP.has(k.toLowerCase())) continue;
      if (typeof v === "string") headers[k] = v;
      else if (Array.isArray(v)) headers[k] = v.join(",");
    }
    if (req.id) headers["x-request-id"] = req.id;

    const init: RequestInit = {
      method: req.method,
      headers,
    };

    if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
      init.body = JSON.stringify(req.body);
      headers["content-type"] = headers["content-type"] ?? "application/json";
    }

    try {
      const upstream = await fetch(target, init);
      res.status(upstream.status);
      upstream.headers.forEach((value, key) => {
        if (HOP_BY_HOP.has(key.toLowerCase())) return;
        res.setHeader(key, value);
      });
      const buf = Buffer.from(await upstream.arrayBuffer());
      res.send(buf);
    } catch (err) {
      logger.warn({ target, err: (err as Error).message }, "upstream forward failed");
      res.status(502).json({ error: "bad_gateway", upstream: baseUrl });
      next();
    }
  };
}
