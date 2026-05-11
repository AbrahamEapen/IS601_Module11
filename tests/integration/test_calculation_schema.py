# tests/integration/test_calculation_schema.py
"""
Tests for Calculation Pydantic schemas.
Verifies that validation, normalisation, and error cases work correctly.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationType,
    CalculationBase,
    CalculationCreate,
    CalculationRead,
    CalculationUpdate,
)


# ---------------------------------------------------------------------------
# CalculationType enum
# ---------------------------------------------------------------------------

def test_enum_values():
    assert CalculationType.ADDITION.value == "addition"
    assert CalculationType.SUBTRACTION.value == "subtraction"
    assert CalculationType.MULTIPLICATION.value == "multiplication"
    assert CalculationType.DIVISION.value == "division"


# ---------------------------------------------------------------------------
# CalculationBase – valid cases
# ---------------------------------------------------------------------------

def test_base_valid_addition():
    calc = CalculationBase(type="addition", a=10.5, b=3.0)
    assert calc.type == CalculationType.ADDITION
    assert calc.a == 10.5
    assert calc.b == 3.0


def test_base_valid_subtraction():
    calc = CalculationBase(type="subtraction", a=20.0, b=5.5)
    assert calc.type == CalculationType.SUBTRACTION


def test_base_valid_multiplication():
    calc = CalculationBase(type="multiplication", a=4.0, b=3.0)
    assert calc.type == CalculationType.MULTIPLICATION
    assert calc.a * calc.b == 12.0


def test_base_valid_division():
    calc = CalculationBase(type="division", a=100.0, b=5.0)
    assert calc.type == CalculationType.DIVISION


def test_base_type_case_insensitive():
    for variant in ["Addition", "ADDITION", "AdDiTiOn"]:
        calc = CalculationBase(type=variant, a=1.0, b=2.0)
        assert calc.type == CalculationType.ADDITION


def test_base_zero_numerator_division_allowed():
    """Zero as 'a' (numerator) is valid for division."""
    calc = CalculationBase(type="division", a=0.0, b=5.0)
    assert calc.a == 0.0


def test_base_negative_numbers():
    calc = CalculationBase(type="addition", a=-5.0, b=-10.0)
    assert calc.a == -5.0
    assert calc.b == -10.0


def test_base_large_numbers():
    calc = CalculationBase(type="multiplication", a=1e10, b=1e10)
    assert isinstance(calc.a, float)


# ---------------------------------------------------------------------------
# CalculationBase – invalid cases
# ---------------------------------------------------------------------------

def test_base_invalid_type():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="modulus", a=10.0, b=3.0)
    assert any("Type must be one of" in str(e) for e in exc.value.errors())


def test_base_division_by_zero():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="division", a=100.0, b=0.0)
    assert any("Cannot divide by zero" in str(e) for e in exc.value.errors())


def test_base_missing_a():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="addition", b=3.0)
    assert any("a" in str(e) for e in exc.value.errors())


def test_base_missing_b():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="addition", a=10.0)
    assert any("b" in str(e) for e in exc.value.errors())


def test_base_non_numeric_a():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", a="not-a-number", b=3.0)


# ---------------------------------------------------------------------------
# CalculationCreate
# ---------------------------------------------------------------------------

def test_create_valid_with_user_id():
    uid = uuid4()
    calc = CalculationCreate(type="multiplication", a=2.0, b=3.0, user_id=str(uid))
    assert calc.type == CalculationType.MULTIPLICATION
    assert calc.user_id == uid


def test_create_valid_without_user_id():
    calc = CalculationCreate(type="addition", a=1.0, b=2.0)
    assert calc.user_id is None


def test_create_invalid_user_id():
    with pytest.raises(ValidationError):
        CalculationCreate(type="subtraction", a=10.0, b=5.0, user_id="not-a-uuid")


def test_create_division_by_zero_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(type="division", a=10.0, b=0.0)


# ---------------------------------------------------------------------------
# CalculationRead
# ---------------------------------------------------------------------------

def _read_payload(**overrides):
    base = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "type": "addition",
        "a": 10.0,
        "b": 5.0,
        "result": 15.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    base.update(overrides)
    return base


def test_read_valid():
    calc = CalculationRead(**_read_payload())
    assert calc.result == 15.0
    assert calc.type == CalculationType.ADDITION


def test_read_without_user_id():
    payload = _read_payload()
    payload["user_id"] = None
    calc = CalculationRead(**payload)
    assert calc.user_id is None


def test_read_missing_result():
    payload = _read_payload()
    del payload["result"]
    with pytest.raises(ValidationError) as exc:
        CalculationRead(**payload)
    assert any("result" in str(e) for e in exc.value.errors())


def test_read_division_by_zero_rejected():
    with pytest.raises(ValidationError):
        CalculationRead(**_read_payload(type="division", b=0.0, result=0.0))


# ---------------------------------------------------------------------------
# CalculationUpdate
# ---------------------------------------------------------------------------

def test_update_valid():
    calc = CalculationUpdate(a=42.0, b=7.0)
    assert calc.a == 42.0
    assert calc.b == 7.0


def test_update_all_optional():
    calc = CalculationUpdate()
    assert calc.a is None
    assert calc.b is None


def test_update_partial():
    calc = CalculationUpdate(a=5.0)
    assert calc.a == 5.0
    assert calc.b is None


# ---------------------------------------------------------------------------
# Cross-type scenario
# ---------------------------------------------------------------------------

def test_multiple_types_via_create():
    uid = uuid4()
    cases = [
        ("addition",       1.0, 2.0),
        ("subtraction",    10.0, 3.0),
        ("multiplication", 2.0, 3.0),
        ("division",       100.0, 5.0),
    ]
    calcs = [CalculationCreate(type=t, a=a, b=b, user_id=str(uid)) for t, a, b in cases]
    assert [c.type for c in calcs] == [
        CalculationType.ADDITION,
        CalculationType.SUBTRACTION,
        CalculationType.MULTIPLICATION,
        CalculationType.DIVISION,
    ]
