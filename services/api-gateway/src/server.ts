import express, { Express, Request, Response, NextFunction } from "express";
import { requestId } from "./middleware/requestId";
import { cors } from "./middleware/cors";
import { rateLimit } from "./middleware/rateLimit";
import { requireAuth, attachUser } from "./middleware/auth";
import { buildForwarder } from "./services/forwarder";
import { logger } from "./logger";

export interface UpstreamConfig {
  auth: string;
  accounts: string;
  txns: string;
  customers: string;
  statements: string;
}

function loadUpstreams(): UpstreamConfig {
  return {
    auth: process.env.AUTH_SERVICE_URL ?? "http://localhost:8082",
    accounts: process.env.ACCOUNT_SERVICE_URL ?? "http://localhost:8083",
    txns: process.env.TXN_SERVICE_URL ?? "http://localhost:8081",
    customers: process.env.CUSTOMER_SERVICE_URL ?? "http://localhost:8086",
    statements: process.env.STATEMENT_SERVICE_URL ?? "http://localhost:8087",
  };
}

export function buildServer(upstreams: UpstreamConfig = loadUpstreams()): Express {
  const app = express();

  // Cap body size at 1 MB; statements / KYC payloads have been observed up to 600 KB.
  app.use(express.json({ limit: "1mb" }));

  app.use(requestId);
  app.use(cors);
  app.use(rateLimit());
  app.use(attachUser);

  // health probes — no auth, no rate limit branch needed
  app.get("/healthz", (_req, res) => res.json({ status: "ok" }));
  app.get("/readyz", (_req, res) => res.json({ status: "ready" }));

  const forwardAuth = buildForwarder(upstreams.auth);
  const forwardAccounts = buildForwarder(upstreams.accounts);
  const forwardTxns = buildForwarder(upstreams.txns);
  const forwardCustomers = buildForwarder(upstreams.customers);
  const forwardStatements = buildForwarder(upstreams.statements);

  // /auth is intentionally public — login/refresh/forgot-password live behind it.
  app.use("/auth", forwardAuth);

  app.use("/accounts", requireAuth, forwardAccounts);
  app.use("/txns", requireAuth, forwardTxns);

  // /customers — fan out to customer-profile-service
  app.use("/customers", forwardCustomers);

  app.use("/statements", requireAuth, forwardStatements);

  // 404
  app.use((req: Request, res: Response) => {
    res.status(404).json({ error: "not_found", path: req.path });
  });

  // error handler
  app.use((err: Error, req: Request, res: Response, _next: NextFunction) => {
    logger.error({ err: err.message, path: req.path }, "gateway error");
    res.status(500).json({ error: "internal_error" });
  });

  return app;
}
