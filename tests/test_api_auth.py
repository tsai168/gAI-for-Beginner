"""WBS-B9 unit tests: U05 JWT/OIDC verification (ADR-0021 §2, Work-2 §4.4).

Exercises the *real* cryptographic verification path against a locally
generated RSA keypair + JWKS — no live IdP needed, same "real, not mocked"
posture as the B7b Temporal tests (`decode_bearer_token(..., jwks=...)`
takes a pre-built JWKS precisely so this is possible without network).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from api.auth import AuthError, decode_bearer_token, role_from_claims
from governance.rbac import UserRole

_ISSUER = "https://idp.example.test/"
_AUDIENCE = "cpo-ai-api"
_KID = "test-key-1"


def _generate_keypair() -> tuple[Any, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _jwks_for(public_key: Any, *, kid: str = _KID) -> dict[str, Any]:
    raw = RSAAlgorithm.to_jwk(public_key)
    jwk: dict[str, Any] = json.loads(raw) if isinstance(raw, str) else dict(raw)
    jwk["kid"] = kid
    jwk["use"] = "sig"
    jwk["alg"] = "RS256"
    return {"keys": [jwk]}


def _sign(private_key: Any, claims: dict[str, Any], *, kid: str = _KID) -> str:
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": kid})


@pytest.fixture
def oidc_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("OIDC_ISSUER", _ISSUER)
    monkeypatch.setenv("OIDC_AUDIENCE", _AUDIENCE)
    yield


def test_valid_token_decodes_and_maps_role(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key)
    token = _sign(
        private_key,
        {"iss": _ISSUER, "aud": _AUDIENCE, "sub": "user-1", "role": "RESEARCH_DIRECTOR"},
    )
    claims = decode_bearer_token(token, jwks=jwks)
    assert role_from_claims(claims) is UserRole.RESEARCH_DIRECTOR


def test_wrong_signing_key_is_rejected(oidc_env: None) -> None:
    private_key, _public_key = _generate_keypair()
    _other_private_key, other_public_key = _generate_keypair()
    jwks = _jwks_for(other_public_key)  # JWKS advertises a DIFFERENT key
    token = _sign(private_key, {"iss": _ISSUER, "aud": _AUDIENCE, "role": "QUANT_RESEARCHER"})
    with pytest.raises(AuthError):
        decode_bearer_token(token, jwks=jwks)


def test_wrong_audience_is_rejected(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key)
    token = _sign(
        private_key, {"iss": _ISSUER, "aud": "some-other-api", "role": "QUANT_RESEARCHER"}
    )
    with pytest.raises(AuthError):
        decode_bearer_token(token, jwks=jwks)


def test_wrong_issuer_is_rejected(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key)
    token = _sign(
        private_key,
        {"iss": "https://not-our-idp.test/", "aud": _AUDIENCE, "role": "QUANT_RESEARCHER"},
    )
    with pytest.raises(AuthError):
        decode_bearer_token(token, jwks=jwks)


def test_unknown_kid_is_rejected(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key, kid="a-different-key-id")
    token = _sign(
        private_key, {"iss": _ISSUER, "aud": _AUDIENCE, "role": "QUANT_RESEARCHER"}, kid=_KID
    )
    with pytest.raises(AuthError, match="no signing key"):
        decode_bearer_token(token, jwks=jwks)


def test_unrecognized_role_claim_is_rejected(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key)
    token = _sign(private_key, {"iss": _ISSUER, "aud": _AUDIENCE, "role": "NOT_A_REAL_ROLE"})
    claims = decode_bearer_token(token, jwks=jwks)
    with pytest.raises(AuthError, match="role"):
        role_from_claims(claims)


def test_missing_role_claim_is_rejected(oidc_env: None) -> None:
    private_key, public_key = _generate_keypair()
    jwks = _jwks_for(public_key)
    token = _sign(private_key, {"iss": _ISSUER, "aud": _AUDIENCE})
    claims = decode_bearer_token(token, jwks=jwks)
    with pytest.raises(AuthError):
        role_from_claims(claims)


def test_missing_env_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    with pytest.raises(RuntimeError, match="OIDC_ISSUER"):
        decode_bearer_token("irrelevant", jwks={"keys": []})
