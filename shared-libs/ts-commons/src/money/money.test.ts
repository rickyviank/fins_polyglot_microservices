import { describe, it, expect } from "vitest";
import { money, usd, plus } from "./money";

describe("Money", () => {
  it("plus sums same currency", () => {
    expect(plus(usd(100), usd(250))).toEqual(usd(350));
  });

  it("rejects currency mismatch", () => {
    expect(() => plus(usd(100), money(100, "EUR"))).toThrow(/currency mismatch/);
  });
});
