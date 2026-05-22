import { Customer } from "../models/customer";

export class CustomerRepo {
  private store = new Map<string, Customer>();

  save(c: Customer): Customer {
    this.store.set(c.id, c);
    return c;
  }

  get(id: string): Customer | undefined {
    return this.store.get(id);
  }

  list(): Customer[] {
    return Array.from(this.store.values());
  }

  findByEmail(email: string): Customer | undefined {
    const e = email.toLowerCase();
    for (const c of this.store.values()) {
      if (c.email.toLowerCase() === e) return c;
    }
    return undefined;
  }
}

export const customerRepo = new CustomerRepo();
