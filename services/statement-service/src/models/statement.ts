import { Money } from "@finspoly/ts-commons";

export interface StatementLine {
  txnId: string;
  postedAt: string;
  description: string;
  amount: Money;
  runningBalance: Money;
}

export interface Statement {
  id: string;
  customerId: string;
  accountNumber: string;
  month: string;
  openingBalance: Money;
  closingBalance: Money;
  lines: StatementLine[];
  generatedAt: string;
}
