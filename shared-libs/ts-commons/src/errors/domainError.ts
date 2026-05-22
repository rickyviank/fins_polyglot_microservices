export class DomainError extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
    this.name = "DomainError";
  }
}

export class ValidationError extends DomainError {
  constructor(message: string) {
    super("VALIDATION_FAILED", message);
    this.name = "ValidationError";
  }
}

export class NotFoundError extends DomainError {
  constructor(resource: string, id: string) {
    super("NOT_FOUND", `${resource} ${id} not found`);
    this.name = "NotFoundError";
  }
}

export class UnauthorizedError extends DomainError {
  constructor(message = "unauthorized") {
    super("UNAUTHORIZED", message);
    this.name = "UnauthorizedError";
  }
}
