export type KycStatus = "pending" | "in_review" | "approved" | "rejected";

export interface Customer {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  ssnEncrypted: string;
  addressLine1: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  kycStatus: KycStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerPublic {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phoneMasked: string;
  ssnLast4: string;
  city: string;
  state: string;
  country: string;
  kycStatus: KycStatus;
  createdAt: string;
}
