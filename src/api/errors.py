"""U05 — API error envelope (WBS-B9, ADR-0021, Work-2 §4.3).

Every 4xx carries a uniform `error_code` (`<MODULE>-ERR-<NNN>`, MODULE =
the owning Work-1 module id, e.g. `K01`, `G01`, or `API` for concerns that
belong to the API layer itself, not any one module); every 5xx would carry
a `correlation_id` for tracing (W05) — none of this layer's endpoints
raise one yet (Postgres/validation errors are the only 5xx sources and
FastAPI's default handler already returns 500 for those uncaught cases).
"""

from __future__ import annotations

import uuid


def format_error_code(module: str, status_code: int) -> str:
    return f"{module}-ERR-{status_code:03d}"


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        module: str,
        message: str,
        correlation_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.module = module
        self.message = message
        self.correlation_id = correlation_id

    @property
    def error_code(self) -> str:
        return format_error_code(self.module, self.status_code)


class UnauthorizedError(ApiError):
    """401 — bearer token missing, malformed, expired, or its claims don't
    map to a known Charter §5 role."""

    def __init__(self, message: str) -> None:
        super().__init__(status_code=401, module="API", message=message)


class ForbiddenError(ApiError):
    """403 — RBAC denial (Work-2 §4.4 / GP-21)."""

    def __init__(self, message: str) -> None:
        super().__init__(status_code=403, module="G05", message=message)


class NotFoundError(ApiError):
    """404."""

    def __init__(self, module: str, message: str) -> None:
        super().__init__(status_code=404, module=module, message=message)


class BadRequestError(ApiError):
    """400 — malformed input or an illegal state transition rejected by the
    owning module (e.g. G01's transition guard, K05's pipeline sequence)."""

    def __init__(self, module: str, message: str) -> None:
        super().__init__(status_code=400, module=module, message=message)


class CflBlockedError(ApiError):
    """409/423 (Work-2 §4.3): CFL-07-style "must never Auto-pass" (409) or
    the row's current cfl_status is BLOCKED (423)."""

    def __init__(self, message: str, *, status_code: int = 409) -> None:
        if status_code not in (409, 423):
            raise ValueError("CflBlockedError status_code must be 409 or 423")
        super().__init__(status_code=status_code, module="G01", message=message)


class NotImplementedYetError(ApiError):
    """501 — the endpoint is real, but the module it depends on isn't built
    yet (R01-R06, WBS-B11). Never silently returns fake data."""

    def __init__(self, module: str, message: str) -> None:
        super().__init__(status_code=501, module=module, message=message)
