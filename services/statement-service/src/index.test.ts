import { describe, it, expect } from "vitest";
import { buildServer } from "./server";

describe("statement-service app", () => {
  it("constructs without throwing", () => {
    const app = buildServer();
    expect(app).toBeDefined();
  });
});
