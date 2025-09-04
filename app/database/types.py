from sqlalchemy.types import UserDefinedType
import enum
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB



class Vector(UserDefinedType):
    def __init__(self, dimensions):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process

class EnumList(TypeDecorator):
    """
    Generic SQLAlchemy type to store a list of Enums
    as PostgreSQL JSONB and convert back to Enum on retrieval.
    Usage:
        colors = mapped_column(EnumList(Color))
    """
    impl = JSONB
    cache_ok = True

    def __init__(self, enum_cls: type[enum.Enum], *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not issubclass(enum_cls, enum.Enum):
            raise TypeError("EnumList requires an Enum subclass")
        self.enum_cls = enum_cls

    def process_bind_param(self, value, dialect):
        """Python -> DB"""
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("EnumList value must be a list of Enums or strings")

        return [
            v.value if isinstance(v, self.enum_cls) else str(v)
            for v in value
        ]

    def process_result_value(self, value, dialect):
        """DB -> Python"""
        if value is None:
            return None
        return [self.enum_cls(v) for v in value]
