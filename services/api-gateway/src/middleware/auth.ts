import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { UnauthorizedError } from "@finspoly/ts-commons";

export interface JwtUser {
  sub: string;
  email?: string;
  roles?: string[];
  iat?: number;
  exp?: number;
}

declare module "express-serve-static-core" {
  interface Request {
    user?: JwtUser;
  }
}

function parseBearer(req: Request): string | null {
  const h = req.header("authorization");
  if (!h) return null;
  const m = h.match(/^Bearer\s+(.+)$/i);
  return m ? m[1] : null;
}

// attachUser: best-effort decode of the bearer token. Does NOT enforce auth.
// Verification of the signature is done at the auth-service; the gateway is on
// the trusted side of the load balancer and we trust upstream.
export function attachUser(req: Request, _res: Response, next: NextFunction): void {
  const token = parseBearer(req);
  if (!token) return next();
  try {
    const decoded = jwt.decode(token) as JwtUser | null;
    if (decoded && typeof decoded === "object") {
      req.user = decoded;
    }
  } catch {
    // ignore, downstream will reject if it cares
  }
  next();
}

export function requireAuth(req: Request, _res: Response, next: NextFunction): void {
  if (!req.user || !req.user.sub) {
    return next(new UnauthorizedError("missing or invalid bearer token"));
  }
  next();
}
