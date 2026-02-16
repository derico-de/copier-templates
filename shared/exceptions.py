"""Custom exceptions for copier templates."""


class CopierTemplateError(Exception):
    """Base exception for copier template errors."""

    pass


class AddonContextError(CopierTemplateError):
    """Raised when no parent addon is detected."""

    pass


class ValidationError(CopierTemplateError):
    """Raised when validation fails."""

    pass
