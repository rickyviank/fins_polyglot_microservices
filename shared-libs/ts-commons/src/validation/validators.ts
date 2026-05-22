const EMAIL = /^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const ACCOUNT_NUMBER = /^\d{10}$/;
const E164 = /^\+[1-9]\d{6,14}$/;
const US_SSN = /^\d{3}-?\d{2}-?\d{4}$/;
const ISO_CURRENCY = /^[A-Z]{3}$/;

export const isEmail         = (s: unknown): s is string => typeof s === "string" && EMAIL.test(s);
export const isAccountNumber = (s: unknown): s is string => typeof s === "string" && ACCOUNT_NUMBER.test(s);
export const isE164Phone     = (s: unknown): s is string => typeof s === "string" && E164.test(s);
export const isUsSsn         = (s: unknown): s is string => typeof s === "string" && US_SSN.test(s);
export const isCurrencyCode  = (s: unknown): s is string => typeof s === "string" && ISO_CURRENCY.test(s);

export function isLuhnValid(cardNumber: string): boolean {
  if (typeof cardNumber !== "string") return false;
  const digits = cardNumber.replace(/\s+/g, "");
  if (!/^\d{13,19}$/.test(digits)) return false;
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = digits.charCodeAt(i) - 48;
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}
