export interface Money {
  readonly minorUnits: number;
  readonly currency: string;
}

const isoCurrency = /^[A-Z]{3}$/;

export function money(minorUnits: number, currency: string): Money {
  if (!Number.isSafeInteger(minorUnits)) {
    throw new Error("minorUnits must be a safe integer");
  }
  const c = currency?.toUpperCase();
  if (!c || !isoCurrency.test(c)) {
    throw new Error("currency must be ISO-4217 3-letter code");
  }
  return Object.freeze({ minorUnits, currency: c });
}

export const usd = (cents: number): Money => money(cents, "USD");

export function plus(a: Money, b: Money): Money {
  if (a.currency !== b.currency) throw new Error(`currency mismatch ${a.currency}/${b.currency}`);
  return money(a.minorUnits + b.minorUnits, a.currency);
}

export function minus(a: Money, b: Money): Money {
  if (a.currency !== b.currency) throw new Error(`currency mismatch ${a.currency}/${b.currency}`);
  return money(a.minorUnits - b.minorUnits, a.currency);
}

export const isNegative = (m: Money): boolean => m.minorUnits < 0;
export const isPositive = (m: Money): boolean => m.minorUnits > 0;
export const isZero     = (m: Money): boolean => m.minorUnits === 0;

export function formatMoney(m: Money): string {
  const sign = m.minorUnits < 0 ? "-" : "";
  const abs = Math.abs(m.minorUnits);
  const major = Math.floor(abs / 100);
  const minor = (abs % 100).toString().padStart(2, "0");
  return `${m.currency} ${sign}${major}.${minor}`;
}
