# Serialization

Beyond accessing model attributes directly via their field names (e.g. `model.foobar`), models can be converted, dumped, serialized, and exported in a number of ways.

## Serialize versus dump

Pydantic uses the terms "serialize" and "dump" interchangeably. Both refer to the process of converting a model to a dictionary or JSON-encoded string.

Outside of Pydantic, the word "serialize" usually refers to converting in-memory data into a string or bytes. However, in the context of Pydantic, there is a very close relationship between converting an object from a more structured form — such as a Pydantic model, a dataclass, etc. — into a less structured form comprised of Python built-ins such as dict.

While we could (and on occasion, do) distinguish between these scenarios by using the word "dump" when converting to primitives and "serialize" when converting to string, for practical purposes, we frequently use the word "serialize" to refer to both of these situations, even though it does not always imply conversion to a string or bytes.

## `model.model_dump(...)`

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

Note that the one exception to sub-models being converted to dictionaries is that `RootModel` and its subclasses will have the `root` field value dumped directly, without a wrapping dictionary. This is also done recursively.

You can use [computed fields](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field) to include `property` and `cached_property` data in the `model.model_dump(...)` output.

Example:

```python
from typing import Any, List, Optional
from pydantic import BaseModel, Field, Json

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})
# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_unset=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=1.1, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=None, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_none=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}

class Model(BaseModel):
    x: List[Json[Any]]

print(Model(x=['{"a": 1}', '[1, 2]']).model_dump())
#> {'x': [{'a': 1}, [1, 2]]}
print(Model(x=['{"a": 1}', '[1, 2]']).model_dump(round_trip=True))
#> {'x': ['{"a":1}', '[1,2]']}
```

## `model.model_dump_json(...)`

The `.model_dump_json()` method serializes a model directly to a JSON-encoded string that is equivalent to the result produced by `.model_dump()`.

Note that Pydantic can serialize many commonly used types to JSON that would otherwise be incompatible with a simple `json.dumps(foobar)` (e.g. `datetime`, `date` or `UUID`).

```python
from datetime import datetime
from pydantic import BaseModel

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel

m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})
print(m.model_dump_json())
#> {"foo":"2032-06-01T12:13:14","bar":{"whatever":123}}
print(m.model_dump_json(indent=2))
"""
{
 "foo": "2032-06-01T12:13:14",
 "bar": {
  "whatever": 123
 }
}
"""
```

## `dict(model)` and iteration

Pydantic models can also be converted to dictionaries using `dict(model)`, and you can also iterate over a model's fields using `for field_name, field_value in model:`. With this approach the raw field values are returned, so sub-models will not be converted to dictionaries.

Example:

```python
from pydantic import BaseModel

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})
print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}
for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123
```

Note also that `RootModel` does get converted to a dictionary with the key 'root'.

## Custom serializers

Pydantic provides several functional serializers to customize how a model is serialized to a dictionary or JSON.

- `@field_serializer`
- `@model_serializer`
- `PlainSerializer`
- `WrapSerializer`

Serialization can be customized on a field using the `@field_serializer` decorator, and on a model using the `@model_serializer` decorator.

Example:

```python
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, field_serializer, model_serializer

class WithCustomEncoders(BaseModel):
    model_config = ConfigDict(ser_json_timedelta='iso8601')
    dt: datetime
    diff: timedelta

    @field_serializer('dt')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()

m = WithCustomEncoders(
    dt=datetime(2032, 6, 1, tzinfo=timezone.utc), diff=timedelta(hours=100)
)
print(m.model_dump_json())
#> {"dt":1969660800.0,"diff":"P4DT4H"}

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {'x': f'serialized {self.x}'}

print(Model(x='test value').model_dump_json())
#> {"x":"serialized test value"}
```

## Overriding the return type when dumping a model

While the return value of `.model_dump()` can usually be described as `dict[str, Any]`, through the use of `@model_serializer` you can actually cause it to return a value that doesn't match this signature:

```python
from pydantic import BaseModel, model_serializer

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x

print(Model(x='not a dict').model_dump())
#> not a dict
```

If you want to do this and still get proper type-checking for this method, you can override `.model_dump()` in an `if TYPE_CHECKING:` block:

```python
from typing import TYPE_CHECKING, Any, Literal
from pydantic import BaseModel, model_serializer

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x

    if TYPE_CHECKING:
        # Ensure type checkers see the correct return type
        def model_dump(
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: Any = None,
            exclude: Any = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool = True,
        ) -> str: ...
```

## Serializing subclasses

### Subclasses of standard types

Subclasses of standard types are automatically dumped like their super-classes:

```python
from datetime import date, timedelta
from typing import Any, Type
from pydantic_core import core_schema
from pydantic import BaseModel, GetCoreSchemaHandler

class DayThisYear(date):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.int_schema(),
            serialization=core_schema.format_ser_schema('%Y-%m-%d'),
        )

    @classmethod
    def validate(cls, v: int):
        return date(2023, 1, 1) + timedelta(days=v)

class FooModel(BaseModel):
    date: DayThisYear

m = FooModel(date=300)
print(m.model_dump_json())
#> {"date":"2023-10-28"}
```

### Subclass instances for fields of `BaseModel`, dataclasses, `TypedDict`

When using fields whose annotations are themselves struct-like types (e.g., `BaseModel` subclasses, dataclasses, etc.), the default behavior is to serialize the attribute value as though it was an instance of the annotated type, even if it is a subclass. More specifically, only the fields from the _annotated_ type will be included in the dumped object:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    user: User

user = UserLogin(name='pydantic', password='hunter2')
m = OuterModel(user=user)
print(m)
#> user=UserLogin(name='pydantic', password='hunter2')
print(m.model_dump()) # note: the password field is not included
#> {'user': {'name': 'pydantic'}}
```

## Serializing with duck-typing

Duck-typing serialization is the behavior of serializing an object based on the fields present in the object itself, rather than the fields present in the schema of the object. This means that when an object is serialized, fields present in a subclass, but not in the original schema, will be included in the serialized output.

This behavior was the default in Pydantic V1, but was changed in V2 to help ensure that you know precisely which fields would be included when serializing, even if subclasses get passed when instantiating the object. This helps prevent security risks when serializing subclasses with sensitive information, for example.

If you want v1-style duck-typing serialization behavior, you can use a runtime setting, or annotate individual types.

- Field / type level: use the `SerializeAsAny` annotation
- Runtime level: use the `serialize_as_any` flag when calling `model_dump()` or `model_dump_json()`

### `SerializeAsAny` annotation

If you want duck-typing serialization behavior, this can be done using the `SerializeAsAny` annotation on a type:

```python
from pydantic import BaseModel, SerializeAsAny

class User(BaseModel):
    name: str

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    as_any: SerializeAsAny[User]
    as_user: User

user = UserLogin(name='pydantic', password='password')
print(OuterModel(as_any=user, as_user=user).model_dump())
#> { 'as_any': {'name': 'pydantic', 'password': 'password'}, 'as_user': {'name': 'pydantic'} }
```

### `serialize_as_any` runtime setting

The `serialize_as_any` runtime setting can be used to serialize model data with or without duck typed serialization behavior. `serialize_as_any` can be passed as a keyword argument to the `model_dump()` and `model_dump_json` methods of `BaseModel`s and `RootModel`s.

If `serialize_as_any` is set to `True`, the model will be serialized using duck typed serialization behavior, which means that the model will ignore the schema and instead ask the object itself how it should be serialized. In particular, this means that when model subclasses are serialized, fields present in the subclass but not in the original schema will be included.

If `serialize_as_any` is set to `False` (which is the default), the model will be serialized using the schema, which means that fields present in a subclass but not in the original schema will be ignored.

## `pickle.dumps(model)`

Pydantic models support efficient pickling and unpickling.

```python
import pickle
from pydantic import BaseModel

class FooBarModel(BaseModel):
    a: str
    b: int

m = FooBarModel(a='hello', b=123)
print(m)
#> a='hello' b=123
data = pickle.dumps(m)
print(data[:20])
#> b'\x80\x04\x95\x95\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main_'
m2 = pickle.loads(data)
print(m2)
#> a='hello' b=123
```

## Advanced include and exclude

The `model_dump` and `model_dump_json` methods support `include` and `exclude` arguments which can either be sets or dictionaries. This allows nested selection of which fields to export:

```python
from pydantic import BaseModel, SecretStr

class User(BaseModel):
    id: int
    username: str
    password: SecretStr

class Transaction(BaseModel):
    id: str
    user: User
    value: int

t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)
# using a set:
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}
# using a dict:
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}
print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

Using `True` indicates that we want to exclude or include an entire key, just as if we included it in a set (note that using `False` isn't supported). This can be done at any depth level.

Special care must be taken when including or excluding fields from a list or tuple of submodels or dictionaries. In this scenario, `model_dump` and related methods expect integer keys for element-wise inclusion or exclusion. To exclude a field from **every** member of a list or tuple, the dictionary key `'__all__'` can be used.

## Model- and field-level include and exclude

In addition to the explicit arguments `exclude` and `include` passed to `model_dump` and `model_dump_json` methods, we can also pass the `exclude: bool` arguments directly to the Field constructor:

Setting `exclude` on the field constructor (`Field(exclude=True)`) takes priority over the `exclude`/`include` on `model_dump` and `model_dump_json`:

```python
from pydantic import BaseModel, Field, SecretStr

class User(BaseModel):
    id: int
    username: str
    password: SecretStr = Field(exclude=True)

class Transaction(BaseModel):
    id: str
    value: int = Field(exclude=True)

t = Transaction(
    id='1234567890',
    value=9876543210,
)
print(t.model_dump())
#> {'id': '1234567890'}
print(t.model_dump(include={'id': True, 'value': True}))
#> {'id': '1234567890'}
```

That being said, setting `exclude` on the field constructor (`Field(exclude=True)`) does not take priority over the `exclude_unset`, `exclude_none`, and `exclude_default` parameters on `model_dump` and `model_dump_json`.