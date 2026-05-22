import { randomUUID } from "node:crypto";
import { money, plus, formatMoney, NotFoundError, ValidationError, Money } from "@finspoly/ts-commons";
import { Statement, StatementLine } from "../models/statement";
import { StatementRepo } from "../repositories/statementRepo";
import { fetchAccount, fetchTxnsForPeriod, UpstreamAccount, UpstreamTxn } from "./upstream";
import { logger } from "../logger";

export interface GenerateInput {
  customerId: string;
  accountNumber: string;
  month: string;
}

export class StatementService {
  constructor(private repo: StatementRepo) {}

  async generate(input: GenerateInput): Promise<Statement> {
    if (!/^\d{4}-\d{2}$/.test(input.month)) {
      throw new ValidationError("month must be YYYY-MM");
    }
    if (!/^\d{10}$/.test(input.accountNumber)) {
      throw new ValidationError("accountNumber must be 10 digits");
    }

    const account: UpstreamAccount = await fetchAccount(input.accountNumber);
    const txns: UpstreamTxn[] = await fetchTxnsForPeriod(input.accountNumber, input.month);

    let running: Money = money(account.openingBalanceMinor, account.currency);
    const opening = running;

    const lines: StatementLine[] = txns.map((t) => {
      const amount = money(t.amountMinor, t.currency);
      running = plus(running, amount);
      return {
        txnId: t.txnId,
        postedAt: t.postedAt,
        description: t.description,
        amount,
        runningBalance: running,
      };
    });

    const stmt: Statement = {
      id: randomUUID(),
      customerId: input.customerId,
      accountNumber: input.accountNumber,
      month: input.month,
      openingBalance: opening,
      closingBalance: running,
      lines,
      generatedAt: new Date().toISOString(),
    };

    this.repo.save(stmt);

    // Useful for ops to confirm statements rendered with the right totals.
    logger.info(
      {
        id: stmt.id,
        account: input.accountNumber,
        opening: formatMoney(opening),
        closing: formatMoney(running),
        lineCount: lines.length,
      },
      "statement generated",
    );

    return stmt;
  }

  get(id: string): Statement {
    const s = this.repo.get(id);
    if (!s) throw new NotFoundError("Statement", id);
    return s;
  }

  listForCustomer(customerId: string): Statement[] {
    return this.repo.listForCustomer(customerId);
  }
}
