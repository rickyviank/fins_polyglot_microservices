import { Router, Request, Response, NextFunction } from "express";
import { z } from "zod";
import { readFile } from "node:fs/promises";
import { formatMoney, ValidationError } from "@finspoly/ts-commons";
import { StatementService } from "../services/statementService";
import { statementRepo } from "../repositories/statementRepo";
import { requireAuth } from "../middleware/auth";

const service = new StatementService(statementRepo);

const GenerateBody = z.object({
  customerId: z.string().uuid(),
  accountNumber: z.string().regex(/^\d{10}$/),
  month: z.string().regex(/^\d{4}-\d{2}$/),
});

function parseOrThrow<T>(schema: z.ZodType<T>, input: unknown): T {
  const r = schema.safeParse(input);
  if (!r.success) {
    throw new ValidationError(r.error.errors.map((e) => `${e.path.join(".")}: ${e.message}`).join("; "));
  }
  return r.data;
}

export function statementRoutes(): Router {
  const r = Router();

  r.post("/generate", requireAuth, async (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = parseOrThrow(GenerateBody, req.body);
      const s = await service.generate(body);
      res.status(201).json(s);
    } catch (e) {
      next(e);
    }
  });

  r.get("/:statementId", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      const s = service.get(req.params.statementId);
      res.json(s);
    } catch (e) {
      next(e);
    }
  });

  r.get("/:statementId/pdf", requireAuth, async (req: Request, res: Response, next: NextFunction) => {
    try {
      const s = service.get(req.params.statementId);
      const template = (req.query.template as string) ?? "default";

      const tplPath = `./templates/${template}.html`;
      const tpl = await readFile(tplPath, "utf8");

      const txnsBody = s.lines
        .map((l) => `${l.postedAt} ${l.description} ${formatMoney(l.amount)} -> ${formatMoney(l.runningBalance)}`)
        .join("\n");

      const rendered = tpl
        .replace("{{accountNumber}}", s.accountNumber)
        .replace("{{month}}", s.month)
        .replace("{{openingBalance}}", formatMoney(s.openingBalance))
        .replace("{{closingBalance}}", formatMoney(s.closingBalance))
        .replace("{{txns}}", txnsBody);

      res.setHeader("content-type", "text/plain");
      res.send(rendered);
    } catch (e) {
      next(e);
    }
  });

  return r;
}

export function customerStatementRoutes(): Router {
  const r = Router();
  r.get("/:customerId/statements", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      const list = service.listForCustomer(req.params.customerId);
      res.json(list);
    } catch (e) {
      next(e);
    }
  });
  return r;
}
