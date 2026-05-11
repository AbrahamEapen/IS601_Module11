# app/models/calculation.py
from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base


class AbstractCalculation:
    """
    Mixin defining shared columns for all calculation types.
    Uses Template Method pattern: base defines interface, subclasses implement get_result().
    """

    @declared_attr
    def __tablename__(cls):
        return 'calculations'

    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    @declared_attr
    def user_id(cls):
        # Nullable: calculations may exist without a user; if set, must be a valid FK.
        return Column(
            UUID(as_uuid=True),
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=True,
            index=True
        )

    @declared_attr
    def type(cls):
        return Column(String(50), nullable=False, index=True)

    @declared_attr
    def a(cls):
        return Column(Float, nullable=False)

    @declared_attr
    def b(cls):
        return Column(Float, nullable=False)

    @declared_attr
    def result(cls):
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, a: float, b: float,
               user_id: uuid.UUID = None) -> "Calculation":
        """
        Factory method: returns the correct Calculation subclass for the given type.

        Args:
            calculation_type: 'addition', 'subtraction', 'multiplication', or 'division'
            a: First operand
            b: Second operand
            user_id: Optional UUID of the owning user

        Raises:
            ValueError: For unsupported calculation types
        """
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        klass = calculation_classes.get(calculation_type.lower())
        if not klass:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return klass(a=a, b=b, user_id=user_id)

    def get_result(self) -> float:
        raise NotImplementedError("Subclasses must implement get_result()")

    def __repr__(self):
        return f"<Calculation(type={self.type}, a={self.a}, b={self.b}, result={self.result})>"


class Calculation(Base, AbstractCalculation):
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }


class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        return self.a + self.b


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        return self.a - self.b


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        return self.a * self.b


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot divide by zero.")
        return self.a / self.b
