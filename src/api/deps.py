"""U05 — FastAPI dependencies: DB session, auth, RBAC (WBS-B9, ADR-0021).

`get_session`/`get_current_role` are the two dependencies tests override
(`app.dependency_overrides[...]`) — DB-backed endpoint tests inject the
integration `db_session` fixture in place of a live connection, and most
endpoint tests fix a `UserRole` directly since `decode_bearer_token`'s real
JWT verification already has its own dedicated tests (`test_api_auth.py`).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from api.auth import AuthError, decode_bearer_token, role_from_claims
from api.errors import ForbiddenError, UnauthorizedError
from governance.rbac import FunctionGroup, UserRole, role_satisfies
from knowledge.db.session import session_scope


def get_session() -> Iterator[Session]:
    with session_scope() as session:
        yield session


def get_current_role(authorization: str | None = Header(default=None)) -> UserRole:
    if authorization is None or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        claims = decode_bearer_token(token)
        return role_from_claims(claims)
    except AuthError as exc:
        raise UnauthorizedError(str(exc)) from exc


def require(group: FunctionGroup) -> Callable[[UserRole], UserRole]:
    def _dependency(role: UserRole = Depends(get_current_role)) -> UserRole:
        if not role_satisfies(role, group):
            raise ForbiddenError(f"{role.value} lacks {group.value} (Work-2 §4.4)")
        return role

    return _dependency
