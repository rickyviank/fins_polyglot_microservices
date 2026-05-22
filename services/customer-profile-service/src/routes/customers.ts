import { Router, Request, Response, NextFunction } from "express";
import { z } from "zod";
import { ValidationError } from "@finspoly/ts-commons";
import { CustomerService } from "../services/customerService";
import { customerRepo } from "../repositories/customerRepo";
import { requireAuth } from "../middleware/auth";

const service = new CustomerService(customerRepo);

const CreateBody = z.object({
  firstName: z.string().min(1),
  lastName: z.string().min(1),
  email: z.string().email(),
  phone: z.string().min(7),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  ssn: z.string().min(9),
  addressLine1: z.string().min(1),
  city: z.string().min(1),
  state: z.string().min(1),
  postalCode: z.string().min(1),
  country: z.string().length(2),
});

const KycBody = z.object({
  status: z.enum(["pending", "in_review", "approved", "rejected"]),
});

function parseOrThrow<T>(schema: z.ZodType<T>, input: unknown): T {
  const r = schema.safeParse(input);
  if (!r.success) {
    throw new ValidationError(r.error.errors.map((e) => `${e.path.join(".")}: ${e.message}`).join("; "));
  }
  return r.data;
}

export function customerRoutes(): Router {
  const r = Router();

  r.post("/", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      const body = parseOrThrow(CreateBody, req.body);
      const c = service.create(body);
      res.status(201).json(c);
    } catch (e) {
      next(e);
    }
  });

  r.get("/:id", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      res.json(service.get(req.params.id));
    } catch (e) {
      next(e);
    }
  });

  r.patch("/:id", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      const c = service.update(req.params.id, req.body ?? {});
      res.json(c);
    } catch (e) {
      next(e);
    }
  });

  // Returns the fully decrypted PII record. Authentication required.
  r.get("/:id/pii", requireAuth, (req: Request, res: Response, next: NextFunction) => {
    try {
      const c = service.getFullPii(req.params.id);
      res.json(c);
    } catch (e) {
      next(e);
    }
  });

  r.post("/:id/kyc-status", (req: Request, res: Response, next: NextFunction) => {
    // Called by kyc-service over the internal mesh.
    try {
      const body = parseOrThrow(KycBody, req.body);
      const c = service.setKycStatus(req.params.id, body.status);
      res.json(c);
    } catch (e) {
      next(e);
    }
  });

  return r;
}
