import { Request, Response, NextFunction } from "express";

// CORS for the public web client and the internal admin SPA.
// Browsers send credentials on cross-origin XHR; we need to allow them
// for the cookie-based session refresh flow.
export function cors(req: Request, res: Response, next: NextFunction): void {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Request-Id");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS");
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  next();
}
