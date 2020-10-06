import os
from collections import namedtuple
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    Optional,
    List,
    Dict,
    cast,
)

FIELD_TYPE_INT = 1
FIELD_TYPE_STRING = 2
FIELD_TYPE_DATETIME = 3
FIELD_TYPE_STRINGMAX = 4
FIELD_TYPE_COMPOSITE = 5


class NoLogicalResult(Exception):
    pass


@dataclass
class Field(object):
    field_type: int
    name: str
    multiple: bool = False
    primary: bool = False
    map_enum_to_id: Optional[dict] = field(default=None, init=False)
    length: Optional[int] = None
    sub_fields: Optional[Sequence] = None
    behaviour: Optional[Dict[str, Any]] = None

    @classmethod
    def enum(cls, name, choices, **kwargs):
        r = cls(FIELD_TYPE_INT, name, **kwargs)
        r.map_enum_to_id = {v: i + 1 for i, v in enumerate(choices)}
        return r

    @classmethod
    def text(cls, name, **kwargs):
        return cls(FIELD_TYPE_STRING, name, **kwargs)

    @classmethod
    def varchar(cls, name, length, **kwargs):
        return cls(FIELD_TYPE_STRINGMAX, name, length=length, **kwargs)

    @classmethod
    def integer(cls, name, **kwargs):
        return cls(FIELD_TYPE_INT, name, **kwargs)

    @classmethod
    def datetime(cls, name, **kwargs):
        return cls(FIELD_TYPE_DATETIME, name, **kwargs)

    @classmethod
    def composite(cls, name, *fields, **kwargs):
        try:
            multiple = kwargs.pop("multiple")
        except KeyError:
            multiple = False

        f = cls(FIELD_TYPE_COMPOSITE, name, multiple=True, **kwargs)

        if multiple:
            for subfield in fields:
                subfield.primary = True

        f.sub_fields = fields
        return f

    def transform(self, v):
        if self.map_enum_to_id:
            return self.map_enum_to_id[v]
        return v

    def __getitem__(self, name):
        for v in (x for x in self.sub_fields if x.name == name):
            return v

        raise KeyError(name)

T = TypeVar("T")

# @dataclass
# class Query(object):
#     OrderBy = namedtuple("OrderBy", ("field", "desc"))
#     Condition = Tuple[Field, str, Any]

#     schema: Schema
#     criteria: List[Condition] = field(default_factory=list)
#     order: Union[OrderBy, List[OrderBy]] = None

#     def to_field(self, field: Union[str, Field]):
#         if isinstance(field, str):
#             return next(f for f in self.schema.fields if f.name == field)
#         return field

#     def restrict(self, field: Union[str, Field], op: str, value: Any) -> Query:
#         nextq = Query(self.schema, self.criteria[:])
#         nextq.criteria.append((self.to_field(field), op, value))
#         return nextq

#     def order_by(self, field: Union[str, Field], desc=False):
#         if not self.order:
#             self.order = self.OrderBy(self.to_field(field), desc)
#         elif isinstance(self.order, self.OrderBy):
#             self.order = [self.order, self.OrderBy(self.to_field(field), desc)]
#         else:
#             self.order.append(self.OrderBy(self.to_field(field), desc))


@dataclass
class Schema(Generic[T]):
    Empty = object()

    table: str
    fields: Sequence[Field]
    expert: Callable[[T], Any]
    first_multi_index: int = field(init=False)
    primary_key: Sequence[Field] = field(init=False)

    def __post_init__(self):
        self.validate_or_error()
        try:
            self.first_multi_index = next(i for i, f in enumerate(self.fields) if f.multiple)
        except StopIteration:
            self.first_multi_index = len(self.fields)

        self.primary_key = tuple(f for f in self.fields if f.primary)

    def validate_or_error(self):
        encountered_first_multi = False
        for f in self.fields:
            if encountered_first_multi and not f.multiple:
                raise ValueError(
                    f"{self.table}: Multi-valued fields need to come after all normal fields."
                )
            if f.multiple:
                encountered_first_multi = True

    def __getitem__(self, name):
        for v in (x for x in self.fields if x.name == name):
            return v
        
        raise KeyError(name)

    def sql_tuples_from_object(self, obj: T):
        expert = self.expert(obj)  # type: ignore
        pk = tuple(getattr(expert, f.name)() for f in self.fields if f.primary)
        single = tuple(
            (field.name, field.transform(getattr(expert, field.name)()))
            for field in self.fields[: self.first_multi_index]
        )
        fields = tuple(x[0] for x in single if x[1] is not Schema.Empty)
        vals = tuple(x[1] for x in single if x[1] is not Schema.Empty)

        multi: List[Tuple] = []
        for field in self.fields[self.first_multi_index :]:
            results = getattr(expert, field.name)()
            if results is Schema.Empty:
                continue

            if field.field_type == FIELD_TYPE_COMPOSITE:
                assert field.sub_fields is not None

                for composite_obj in results:
                    tf = tuple(sf.transform(x) for sf, x in zip(field.sub_fields, composite_obj))
                    multi.append((field.name, pk + tf))
            else:
                multi.extend((field.name, pk + (field.transform(x),)) for x in results)

        return (fields, vals), multi


##############################################################################
