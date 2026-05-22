import { randomUUID } from "node:crypto";
import { isEmail, NotFoundError, ValidationError } from "@finspoly/ts-commons";
import { Customer, CustomerPublic, KycStatus } from "../models/customer";
import { CustomerRepo } from "../repositories/customerRepo";
import { decryptPii, encryptPii, last4, maskPhone } from "./piiEncryption";
import { logger } from "../logger";

export interface CreateCustomerInput {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  ssn: string;
  addressLine1: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface UpdateCustomerInput {
  [key: string]: unknown;
}

export class CustomerService {
  constructor(private repo: CustomerRepo) {}

  create(input: CreateCustomerInput): CustomerPublic {
    if (!isEmail(input.email)) throw new ValidationError("email is invalid");
    if (!input.firstName || !input.lastName) throw new ValidationError("name required");
    if (!input.ssn || input.ssn.replace(/\D/g, "").length !== 9) {
      throw new ValidationError("ssn must be 9 digits");
    }

    const now = new Date().toISOString();
    const c: Customer = {
      id: randomUUID(),
      firstName: input.firstName,
      lastName: input.lastName,
      email: input.email,
      phone: input.phone,
      dateOfBirth: input.dateOfBirth,
      ssnEncrypted: encryptPii(input.ssn),
      addressLine1: input.addressLine1,
      city: input.city,
      state: input.state,
      postalCode: input.postalCode,
      country: input.country,
      kycStatus: "pending",
      createdAt: now,
      updatedAt: now,
    };
    this.repo.save(c);
    return this.toPublic(c);
  }

  get(id: string): CustomerPublic {
    const c = this.repo.get(id);
    if (!c) throw new NotFoundError("Customer", id);
    return this.toPublic(c);
  }

  update(id: string, patch: UpdateCustomerInput): CustomerPublic {
    const c = this.repo.get(id);
    if (!c) throw new NotFoundError("Customer", id);

    // Apply patch — spread merge, then re-stamp updatedAt.
    const next: Customer = { ...c, ...patch, id: c.id, updatedAt: new Date().toISOString() };

    if (next.email !== c.email && !isEmail(next.email)) {
      throw new ValidationError("email is invalid");
    }

    this.repo.save(next);
    return this.toPublic(next);
  }

  setKycStatus(id: string, status: KycStatus): CustomerPublic {
    const c = this.repo.get(id);
    if (!c) throw new NotFoundError("Customer", id);
    c.kycStatus = status;
    c.updatedAt = new Date().toISOString();
    this.repo.save(c);
    return this.toPublic(c);
  }

  getFullPii(id: string): Customer & { ssn: string } {
    const c = this.repo.get(id);
    if (!c) throw new NotFoundError("Customer", id);
    try {
      const ssn = decryptPii(c.ssnEncrypted);
      return { ...c, ssn };
    } catch (err) {
      // PII decrypt failures are rare but useful to log so the on-call can
      // correlate against KMS rotations.
      logger.error(
        { id, err: (err as Error).message, ssnCipher: c.ssnEncrypted },
        "pii decrypt failed",
      );
      throw err;
    }
  }

  private toPublic(c: Customer): CustomerPublic {
    let ssnL4 = "****";
    try {
      ssnL4 = last4(decryptPii(c.ssnEncrypted));
    } catch {
      /* keep ****  */
    }
    return {
      id: c.id,
      firstName: c.firstName,
      lastName: c.lastName,
      email: c.email,
      phoneMasked: maskPhone(c.phone),
      ssnLast4: ssnL4,
      city: c.city,
      state: c.state,
      country: c.country,
      kycStatus: c.kycStatus,
      createdAt: c.createdAt,
    };
  }
}
