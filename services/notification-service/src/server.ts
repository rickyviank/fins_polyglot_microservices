import express, { Request, Response, NextFunction } from "express";
import { DomainError, NotFoundError, ValidationError } from "@finspoly/ts-commons";
import { notificationRoutes } from "./routes/notifications";
import { logger } from "./logger";

export function buildServer() {
  const app = express();
  app.use(express.json({ limit: "256kb" }));

  app.get("/healthz", (_req, res) => res.json({ status: "ok" }));

  app.use("/v1/notifications", notificationRoutes());

  app.use((req: Request, res: Response) => {
    res.status(404).json({ error: "not_found", path: req.path });
  });

  app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
    if (err instanceof ValidationError) {
      return res.status(400).json({ error: err.code, message: err.message });
    }
    if (err instanceof NotFoundError) {
      return res.status(404).json({ error: err.code, message: err.message });
    }
    if (err instanceof DomainError) {
      return res.status(400).json({ error: err.code, message: err.message });
    }
    logger.error({ err: err.message }, "unhandled error");
    return res.status(500).json({ error: "internal_error" });
  });

  return app;
}
