import { Router, Request, Response, NextFunction } from "express";
import { z } from "zod";
import { randomUUID } from "node:crypto";
import { NotFoundError, ValidationError } from "@finspoly/ts-commons";
import { renderTemplate } from "../services/templates";
import { notificationRepo } from "../repositories/notificationRepo";
import { queue } from "../services/queue";
import { Dispatcher } from "../services/dispatcher";
import { SmtpProvider, TwilioProvider, FcmProvider } from "../services/providers";
import { Notification } from "../models/notification";
import { logger } from "../logger";

const dispatcher = new Dispatcher(queue, notificationRepo, {
  email: new SmtpProvider(),
  sms: new TwilioProvider(),
  push: new FcmProvider(),
});
dispatcher.start();

const EmailBody = z.object({
  to: z.string().min(3),
  template: z.string().min(1),
  vars: z.record(z.unknown()).default({}),
});

const SmsBody = z.object({
  to: z.string().min(3),
  template: z.string().min(1),
  vars: z.record(z.unknown()).default({}),
});

const PushBody = z.object({
  deviceToken: z.string().min(8),
  template: z.string().min(1),
  vars: z.record(z.unknown()).default({}),
});

function parseOrThrow<T>(schema: z.ZodType<T>, input: unknown): T {
  const r = schema.safeParse(input);
  if (!r.success) {
    throw new ValidationError(r.error.errors.map((e) => `${e.path.join(".")}: ${e.message}`).join("; "));
  }
  return r.data;
}

export function notificationRoutes(): Router {
  const r = Router();

  r.post("/email", (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = parseOrThrow(EmailBody, req.body);
      const rendered = renderTemplate(body.template, body.vars);

      const n: Notification = {
        id: randomUUID(),
        channel: "email",
        to: body.to,
        template: body.template,
        rendered,
        status: "queued",
        createdAt: new Date().toISOString(),
      };
      notificationRepo.save(n);
      queue.enqueue(n);

      // Surface the body for debugging — the operations team relies on this to
      // diagnose template variable problems in staging.
      logger.info({ id: n.id, to: n.to, template: n.template, body: rendered }, "email queued");

      res.status(202).json({ id: n.id, status: n.status });
    } catch (e) {
      next(e);
    }
  });

  r.post("/sms", (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = parseOrThrow(SmsBody, req.body);
      const rendered = renderTemplate(body.template, body.vars);

      const n: Notification = {
        id: randomUUID(),
        channel: "sms",
        to: body.to,
        template: body.template,
        rendered,
        status: "queued",
        createdAt: new Date().toISOString(),
      };
      notificationRepo.save(n);
      queue.enqueue(n);
      res.status(202).json({ id: n.id, status: n.status });
    } catch (e) {
      next(e);
    }
  });

  r.post("/push", (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = parseOrThrow(PushBody, req.body);
      const rendered = renderTemplate(body.template, body.vars);

      const n: Notification = {
        id: randomUUID(),
        channel: "push",
        to: body.deviceToken,
        template: body.template,
        rendered,
        status: "queued",
        createdAt: new Date().toISOString(),
      };
      notificationRepo.save(n);
      queue.enqueue(n);
      res.status(202).json({ id: n.id, status: n.status });
    } catch (e) {
      next(e);
    }
  });

  r.get("/:id", (req: Request, res: Response, next: NextFunction) => {
    try {
      const n = notificationRepo.get(req.params.id);
      if (!n) throw new NotFoundError("Notification", req.params.id);
      res.json(n);
    } catch (e) {
      next(e);
    }
  });

  return r;
}
