import { z } from "zod";

export const CustomerIdSchema = z.string().uuid();
export const AccountNumberSchema = z.string().regex(/^\d{10}$/, "must be 10 digits");
export const CurrencySchema = z.string().regex(/^[A-Z]{3}$/);
export const MoneySchema = z.object({
  minorUnits: z.number().int(),
  currency: CurrencySchema,
});

export const PageQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(200).default(50),
  offset: z.coerce.number().int().min(0).default(0),
});

export type CustomerId = z.infer<typeof CustomerIdSchema>;
export type AccountNumber = z.infer<typeof AccountNumberSchema>;
export type PageQuery = z.infer<typeof PageQuerySchema>;
