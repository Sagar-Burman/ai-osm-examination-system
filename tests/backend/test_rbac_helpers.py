import pytest
from fastapi import HTTPException

from app.core.deps import require_role, require_roles


def test_require_role_allows_matching_role():
    checker = require_role("admin")
    payload = {"role": "admin"}

    assert checker(payload) == payload


def test_require_role_rejects_wrong_role():
    checker = require_role("admin")

    with pytest.raises(HTTPException) as exc:
        checker({"role": "examiner"})

    assert exc.value.status_code == 403
    assert exc.value.detail == "Insufficient permissions"


def test_require_roles_allows_any_declared_role():
    checker = require_roles("admin", "moderator")

    assert checker({"role": "moderator"})["role"] == "moderator"


def test_require_roles_rejects_undeclared_role():
    checker = require_roles("admin", "moderator")

    with pytest.raises(HTTPException) as exc:
        checker({"role": "examiner"})

    assert exc.value.status_code == 403
