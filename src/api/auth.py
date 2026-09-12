"""U05 — Authentication: OAuth2/OIDC bearer JWT (WBS-B9, ADR-0021, Work-2
§4.4).

`OIDC_ISSUER` / `OIDC_AUDIENCE` / `OIDC_JWKS_URL` come from environment
variables only (CLAUDE.md §9 — never hardcoded). `fetch_jwks` is the one
function that makes a live network call; it is kept separate and thin so
`decode_bearer_token`'s actual cryptographic verification can be exercised
end-to-end in tests against a locally generated RSA keypair (no live IdP
needed) — the same "real, not mocked" posture as the B7b Temporal tests.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import jwt
from jwt import PyJWKSet

from governance.rbac import UserRole


class AuthError(PermissionError):
    """Bearer token missing, malformed, expired, or its claims don't map to
    a known Charter §5 role."""


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set (CLAUDE.md §9 — no hardcoded secrets)")
    return value


def fetch_jwks(jwks_url: str) -> dict[str, Any]:
    response = httpx.get(jwks_url, timeout=5.0)
    response.raise_for_status()
    jwks: dict[str, Any] = response.json()
    return jwks


def _resolve_signing_key(token: str, jwks: dict[str, Any]) -> Any:
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError as exc:
        raise AuthError(f"malformed token header: {exc}") from exc
    key_set = PyJWKSet.from_dict(jwks)
    for key in key_set.keys:
        if key.key_id == kid:
            return key.key
    raise AuthError(f"no signing key found for kid={kid!r}")


def decode_bearer_token(token: str, *, jwks: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verifies signature, issuer and audience, then returns the claims.
    `jwks` is normally omitted (fetched from `OIDC_JWKS_URL`); tests pass a
    locally built JWKS instead of hitting a real IdP."""
    issuer = _env("OIDC_ISSUER")
    audience = _env("OIDC_AUDIENCE")
    resolved_jwks = jwks if jwks is not None else fetch_jwks(_env("OIDC_JWKS_URL"))
    signing_key = _resolve_signing_key(token, resolved_jwks)
    try:
        claims: dict[str, Any] = jwt.decode(
            token, signing_key, algorithms=["RS256"], audience=audience, issuer=issuer
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc
    return claims


_ROLE_CLAIM = "role"
_CLAIM_TO_ROLE: dict[str, UserRole] = {r.value: r for r in UserRole}


def role_from_claims(claims: dict[str, Any]) -> UserRole:
    raw = claims.get(_ROLE_CLAIM)
    role = _CLAIM_TO_ROLE.get(raw) if isinstance(raw, str) else None
    if role is None:
        raise AuthError(f"claims carry no recognized {_ROLE_CLAIM!r} (Charter §5 role): {raw!r}")
    return role
