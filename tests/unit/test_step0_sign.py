"""D-62: digest-always, HMAC-when-secret Step-0 signing."""

from __future__ import annotations

from pursuit.security import step0_sign

_DECLARATION = {"role": "police", "team_code": "khm-mn17", "commit_hash": "abc123"}
_SECRET = "a-shared-league-secret"


def test_sign_declaration_without_a_secret_is_explicitly_unsigned():
    signature = step0_sign.sign_declaration(_DECLARATION, secret=None)
    assert signature["signed"] is False
    assert signature["hmac"] is None
    assert signature["digest"] == step0_sign.digest_declaration(_DECLARATION)


def test_sign_declaration_with_a_secret_is_signed_and_verifies():
    signature = step0_sign.sign_declaration(_DECLARATION, secret=_SECRET)
    assert signature["signed"] is True
    assert signature["hmac"] is not None
    assert step0_sign.verify_declaration(
        _DECLARATION, digest=signature["digest"], hmac_value=signature["hmac"], secret=_SECRET,
    ) is True


def test_verify_declaration_fails_after_flipping_any_one_field():
    signature = step0_sign.sign_declaration(_DECLARATION, secret=_SECRET)
    for key in _DECLARATION:
        tampered = {**_DECLARATION, key: f"{_DECLARATION[key]}-tampered"}
        assert step0_sign.verify_declaration(
            tampered, digest=signature["digest"], hmac_value=signature["hmac"], secret=_SECRET,
        ) is False


def test_verify_declaration_fails_with_the_wrong_secret():
    signature = step0_sign.sign_declaration(_DECLARATION, secret=_SECRET)
    assert step0_sign.verify_declaration(
        _DECLARATION, digest=signature["digest"], hmac_value=signature["hmac"], secret="wrong",
    ) is False


def test_a_digest_only_unsigned_declaration_still_verifies_its_digest():
    signature = step0_sign.sign_declaration(_DECLARATION, secret=None)
    assert step0_sign.verify_declaration(
        _DECLARATION, digest=signature["digest"], hmac_value=None, secret=None,
    ) is True
    tampered = {**_DECLARATION, "role": "thief"}
    assert step0_sign.verify_declaration(
        tampered, digest=signature["digest"], hmac_value=None, secret=None,
    ) is False
