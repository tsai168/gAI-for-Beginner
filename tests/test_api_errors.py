"""WBS-B9 unit tests: U05 error envelope (ADR-0021 §2, Work-2 §4.3)."""

from __future__ import annotations

import uuid

import pytest

from api.errors import (
    BadRequestError,
    CflBlockedError,
    ForbiddenError,
    NotFoundError,
    NotImplementedYetError,
    UnauthorizedError,
    format_error_code,
)


def test_format_error_code() -> None:
    assert format_error_code("K01", 404) == "K01-ERR-404"
    assert format_error_code("G01", 9) == "G01-ERR-009"


def test_unauthorized_is_401_api_module() -> None:
    exc = UnauthorizedError("no token")
    assert exc.status_code == 401
    assert exc.error_code == "API-ERR-401"


def test_forbidden_is_403_g05_module() -> None:
    exc = ForbiddenError("lacks READ")
    assert exc.status_code == 403
    assert exc.error_code == "G05-ERR-403"


def test_not_found_uses_caller_module() -> None:
    exc = NotFoundError("K05", "event not found")
    assert exc.status_code == 404
    assert exc.error_code == "K05-ERR-404"


def test_bad_request_uses_caller_module() -> None:
    exc = BadRequestError("G01", "illegal transition")
    assert exc.status_code == 400
    assert exc.error_code == "G01-ERR-400"


def test_cfl_blocked_defaults_to_409() -> None:
    exc = CflBlockedError("must not auto-pass")
    assert exc.status_code == 409
    assert exc.module == "G01"


def test_cfl_blocked_accepts_423() -> None:
    exc = CflBlockedError("row is BLOCKED", status_code=423)
    assert exc.status_code == 423


def test_cfl_blocked_rejects_other_status_codes() -> None:
    with pytest.raises(ValueError, match="409 or 423"):
        CflBlockedError("nope", status_code=400)


def test_not_implemented_yet_is_501() -> None:
    exc = NotImplementedYetError("R03", "dashboard not built")
    assert exc.status_code == 501
    assert exc.error_code == "R03-ERR-501"


def test_correlation_id_round_trips() -> None:
    cid = uuid.uuid4()
    exc = UnauthorizedError("x")
    exc.correlation_id = cid
    assert exc.correlation_id == cid
