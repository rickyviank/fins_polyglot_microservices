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

export function requireAuth(req: Request, _res: Response, next: NextFunction): void {
  const sub = req.header("x-user-id");
  if (!sub) return next(new UnauthorizedError("missing user identity"));
  req.user = {
    sub,
    roles: (req.header("x-user-roles") ?? "").split(",").map((s) => s.trim()).filter(Boolean),
  };
  next();
}
