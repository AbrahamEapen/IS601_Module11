# tests/integration/test_db_calculation.py
"""
Database integration tests for the Calculation model.

These tests require a running PostgreSQL instance. In CI they run against
the postgres service container defined in the GitHub Actions workflow.
Locally, start the DB with: docker compose up -d db

Each test runs inside a rolled-back transaction so the database is left
clean after every test (see conftest.py).
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def flush_and_reload(session, obj):
    """Flush obj to DB within the current transaction and return a fresh copy."""
    session.flush()
    session.expire(obj)
    return obj


# ---------------------------------------------------------------------------
# Insert and read back tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("calc_type,a,b,expected", [
    ("addition",       10.0, 5.0,  15.0),
    ("subtraction",    10.0, 3.0,   7.0),
    ("multiplication",  4.0, 3.0,  12.0),
    ("division",       20.0, 4.0,   5.0),
])
def test_insert_and_read_back(db_session, calc_type, a, b, expected):
    """Insert a calculation, compute result, flush to DB, and verify stored values."""
    calc = Calculation.create(calc_type, a=a, b=b)
    calc.result = calc.get_result()
    db_session.add(calc)
    flush_and_reload(db_session, calc)

    assert calc.result == expected
    assert calc.a == a
    assert calc.b == b
    assert calc.type == calc_type


def test_insert_with_user_fk(db_session, test_user):
    """Calculation with a valid user_id FK is stored correctly."""
    calc = Calculation.create("addition", a=3.0, b=7.0, user_id=test_user.id)
    calc.result = calc.get_result()
    db_session.add(calc)
    flush_and_reload(db_session, calc)

    assert calc.user_id == test_user.id
    assert calc.result == 10.0


def test_insert_without_user_id(db_session):
    """Calculation without a user_id (anonymous) is accepted by the DB."""
    calc = Calculation.create("multiplication", a=6.0, b=7.0)
    calc.result = calc.get_result()
    db_session.add(calc)
    flush_and_reload(db_session, calc)

    assert calc.user_id is None
    assert calc.result == 42.0


def test_query_by_type(db_session):
    """Filtering calculations by type returns only matching rows."""
    for t, a, b in [("addition", 1, 2), ("addition", 3, 4), ("subtraction", 10, 3)]:
        c = Calculation.create(t, a=a, b=b)
        c.result = c.get_result()
        db_session.add(c)
    db_session.flush()

    additions = db_session.query(Calculation).filter(Calculation.type == "addition").all()
    assert len(additions) == 2
    assert all(isinstance(c, Addition) for c in additions)


def test_polymorphic_query_returns_correct_subclass(db_session):
    """SQLAlchemy resolves the correct subclass from the discriminator column."""
    pairs = [
        ("addition",       Addition,       5.0,  3.0),
        ("subtraction",    Subtraction,    5.0,  3.0),
        ("multiplication", Multiplication, 5.0,  3.0),
        ("division",       Division,       9.0,  3.0),
    ]
    for t, klass, a, b in pairs:
        c = Calculation.create(t, a=a, b=b)
        c.result = c.get_result()
        db_session.add(c)
    db_session.flush()

    for t, klass, _, _ in pairs:
        row = db_session.query(Calculation).filter(Calculation.type == t).first()
        assert isinstance(row, klass)


# ---------------------------------------------------------------------------
# Error / invalid input tests
# ---------------------------------------------------------------------------

def test_division_by_zero_model_raises(db_session):
    """Division.get_result() raises before any DB interaction."""
    calc = Division(a=10.0, b=0.0)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.get_result()


def test_factory_invalid_type_raises(db_session):
    """Factory rejects unsupported operation types before touching the DB."""
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create("power", a=2.0, b=8.0)


def test_missing_required_column_raises(db_session):
    """Inserting a Calculation without 'a' or 'b' raises a DB error."""
    from sqlalchemy.exc import IntegrityError, StatementError
    calc = Addition()  # a and b are NOT NULL in the schema
    calc.result = None
    db_session.add(calc)
    with pytest.raises((IntegrityError, StatementError)):
        db_session.flush()
    db_session.rollback()


def test_invalid_user_id_fk_raises(db_session):
    """Referencing a non-existent user_id violates the FK constraint."""
    from sqlalchemy.exc import IntegrityError
    fake_uid = uuid.uuid4()
    calc = Calculation.create("addition", a=1.0, b=1.0, user_id=fake_uid)
    calc.result = calc.get_result()
    db_session.add(calc)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
