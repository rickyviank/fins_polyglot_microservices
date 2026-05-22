class DomainError(Exception):
    code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class ValidationError(DomainError):
    code = "VALIDATION_FAILED"


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class UnauthorizedError(DomainError):
    code = "UNAUTHORIZED"
