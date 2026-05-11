# tests/integration/test_calculation.py
"""
Tests for polymorphic Calculation model logic (no database required).
Covers the factory pattern and per-subclass get_result() behaviour.
"""

import pytest
import uuid

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)


def make_uid():
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Individual subclass get_result() tests
# ---------------------------------------------------------------------------

def test_addition_get_result():
    calc = Addition(user_id=make_uid(), a=10, b=5.5)
    assert calc.get_result() == 15.5


def test_subtraction_get_result():
    calc = Subtraction(user_id=make_uid(), a=20, b=5)
    assert calc.get_result() == 15


def test_multiplication_get_result():
    calc = Multiplication(user_id=make_uid(), a=3, b=4)
    assert calc.get_result() == 12


def test_division_get_result():
    calc = Division(user_id=make_uid(), a=100, b=5)
    assert calc.get_result() == 20.0


def test_division_by_zero_raises():
    calc = Division(user_id=make_uid(), a=50, b=0)
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        calc.get_result()


# ---------------------------------------------------------------------------
# Factory pattern tests
# ---------------------------------------------------------------------------

def test_factory_returns_addition():
    calc = Calculation.create('addition', a=1, b=2, user_id=make_uid())
    assert isinstance(calc, Addition)
    assert isinstance(calc, Calculation)
    assert calc.get_result() == 3


def test_factory_returns_subtraction():
    calc = Calculation.create('subtraction', a=10, b=4, user_id=make_uid())
    assert isinstance(calc, Subtraction)
    assert calc.get_result() == 6


def test_factory_returns_multiplication():
    calc = Calculation.create('multiplication', a=3, b=4, user_id=make_uid())
    assert isinstance(calc, Multiplication)
    assert calc.get_result() == 12


def test_factory_returns_division():
    calc = Calculation.create('division', a=100, b=5, user_id=make_uid())
    assert isinstance(calc, Division)
    assert calc.get_result() == 20.0


def test_factory_invalid_type_raises():
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create('modulus', a=10, b=3, user_id=make_uid())


def test_factory_case_insensitive():
    for variant in ['addition', 'Addition', 'ADDITION', 'AdDiTiOn']:
        calc = Calculation.create(variant, a=5, b=3, user_id=make_uid())
        assert isinstance(calc, Addition)
        assert calc.get_result() == 8


def test_factory_without_user_id():
    """Factory must accept None user_id (anonymous calculations allowed)."""
    calc = Calculation.create('addition', a=2, b=3)
    assert isinstance(calc, Addition)
    assert calc.user_id is None


# ---------------------------------------------------------------------------
# Polymorphic behaviour
# ---------------------------------------------------------------------------

def test_polymorphic_list():
    uid = make_uid()
    calcs = [
        Calculation.create('addition',       a=1,   b=2,  user_id=uid),
        Calculation.create('subtraction',    a=10,  b=3,  user_id=uid),
        Calculation.create('multiplication', a=2,   b=3,  user_id=uid),
        Calculation.create('division',       a=100, b=5,  user_id=uid),
    ]
    results = [c.get_result() for c in calcs]
    assert results == [3, 7, 6, 20.0]


@pytest.mark.parametrize("calc_type,a,b,expected", [
    ('addition',       10, 2, 12),
    ('subtraction',    10, 2,  8),
    ('multiplication', 10, 2, 20),
    ('division',       10, 2,  5.0),
])
def test_polymorphic_dispatch(calc_type, a, b, expected):
    calc = Calculation.create(calc_type, a=a, b=b, user_id=make_uid())
    assert calc.get_result() == expected
