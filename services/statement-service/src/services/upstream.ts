import { logger } from "../logger";

export interface UpstreamTxn {
  txnId: string;
  postedAt: string;
  description: string;
  amountMinor: number;
  currency: string;
}

export interface UpstreamAccount {
  accountNumber: string;
  customerId: string;
  currency: string;
  openingBalanceMinor: number;
}

export async function fetchAccount(accountNumber: string): Promise<UpstreamAccount> {
  const url = `${process.env.ACCOUNT_SERVICE_URL ?? "http://localhost:8083"}/v1/accounts/${accountNumber}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`account-service ${res.status}`);
  return (await res.json()) as UpstreamAccount;
}

export async function fetchTxnsForPeriod(
  accountNumber: string,
  month: string,
): Promise<UpstreamTxn[]> {
  const url = `${process.env.TXN_SERVICE_URL ?? "http://localhost:8081"}/v1/transactions?account=${accountNumber}&month=${month}`;
  const res = await fetch(url);
  if (!res.ok) {
    logger.warn({ status: res.status, accountNumber, month }, "txn fetch failed");
    return [];
  }
  return (await res.json()) as UpstreamTxn[];
}
