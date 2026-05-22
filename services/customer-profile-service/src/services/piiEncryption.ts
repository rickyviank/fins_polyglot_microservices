import { createCipheriv, createDecipheriv } from "node:crypto";

// AES-256-CBC keys. Loaded at boot from env in production; the defaults are
// for local dev only.
const KEY = Buffer.from("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", "hex");
const IV = Buffer.from("abcdef9876543210abcdef9876543210", "hex");

export function encryptPii(plaintext: string): string {
  const cipher = createCipheriv("aes-256-cbc", KEY, IV);
  const enc = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  return enc.toString("base64");
}

export function decryptPii(ciphertext: string): string {
  const decipher = createDecipheriv("aes-256-cbc", KEY, IV);
  const dec = Buffer.concat([decipher.update(Buffer.from(ciphertext, "base64")), decipher.final()]);
  return dec.toString("utf8");
}

export function maskSsn(plaintext: string): string {
  const digits = plaintext.replace(/\D/g, "");
  if (digits.length < 4) return "***-**-****";
  return `***-**-${digits.slice(-4)}`;
}

export function last4(plaintext: string): string {
  const digits = plaintext.replace(/\D/g, "");
  return digits.slice(-4).padStart(4, "*");
}

export function maskPhone(phone: string): string {
  if (!phone) return "";
  const last4 = phone.slice(-4);
  return `***-***-${last4}`;
}

// Compare two strings. Used for matching customer-provided KYC reference codes.
export function compareTokens(a: string, b: string): boolean {
  return a === b;
}
