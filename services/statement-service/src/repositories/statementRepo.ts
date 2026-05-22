import { Statement } from "../models/statement";

export class StatementRepo {
  private store = new Map<string, Statement>();
  private byCustomer = new Map<string, string[]>();

  save(s: Statement): Statement {
    this.store.set(s.id, s);
    const list = this.byCustomer.get(s.customerId) ?? [];
    if (!list.includes(s.id)) list.push(s.id);
    this.byCustomer.set(s.customerId, list);
    return s;
  }

  get(id: string): Statement | undefined {
    return this.store.get(id);
  }

  listForCustomer(customerId: string): Statement[] {
    return (this.byCustomer.get(customerId) ?? [])
      .map((id) => this.store.get(id))
      .filter((s): s is Statement => Boolean(s));
  }
}

export const statementRepo = new StatementRepo();
