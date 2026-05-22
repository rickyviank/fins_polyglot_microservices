import { describe, it, expect } from "vitest";
import { rateLimit } from "./rateLimit";
import type { Request, Response } from "express";

function mockReq(ip = "1.2.3.4"): Request {
  return {
    headers: { "x-forwarded-for": ip },
    socket: { remoteAddress: ip },
  } as unknown as Request;
}

function mockRes() {
  const res: Partial<Response> & { _status?: number } = {};
  res.status = (code: number) => {
    res._status = code;
    return res as Response;
  };
  res.json = () => res as Response;
  return res as Response & { _status?: number };
}

describe("rateLimit middleware", () => {
  it("blocks the (capacity+1)th request from the same IP with 429", () => {
    const mw = rateLimit({ capacity: 2, refillPerSec: 0 });
    const next = () => {};
    mw(mockReq("9.9.9.9"), mockRes(), next);
    mw(mockReq("9.9.9.9"), mockRes(), next);
    const res = mockRes();
    mw(mockReq("9.9.9.9"), res, next);
    expect(res._status).toBe(429);
  });
});
