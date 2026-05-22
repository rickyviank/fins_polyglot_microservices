import { Request, Response, NextFunction } from "express";
import { UnauthorizedError } from "@finspoly/ts-commons";

export interface AuthUser {
  sub: string;
  roles?: string[];
}

declare module "express-serve-static-core" {
  interface Request {
    user?: AuthUser;
  }
}

// The gateway already decoded the bearer JWT and forwards the claims in
// `x-user-id` / `x-user-roles`. We use those.
export function requireAuth(req: Request, _res: Response, next: NextFunction): void {
  const sub = req.header("x-user-id");
  if (!sub) return next(new UnauthorizedError("missing user identity"));
  const rolesHeader = req.header("x-user-roles") ?? "";
  req.user = { sub, roles: rolesHeader.split(",").map((s) => s.trim()).filter(Boolean) };
  next();
}
