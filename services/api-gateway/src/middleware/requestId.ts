import { Request, Response, NextFunction } from "express";
import { randomUUID } from "node:crypto";

declare module "express-serve-static-core" {
  interface Request {
    id?: string;
  }
}

const HEADER = "x-request-id";

export function requestId(req: Request, res: Response, next: NextFunction): void {
  const incoming = req.header(HEADER);
  const id = incoming && incoming.length > 0 && incoming.length <= 128 ? incoming : randomUUID();
  req.id = id;
  res.setHeader(HEADER, id);
  next();
}
