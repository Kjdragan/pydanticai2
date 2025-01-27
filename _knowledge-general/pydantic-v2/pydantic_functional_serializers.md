# Functional Serializers

This module contains related classes and functions for serialization.

## FieldPlainSerializer

```python
FieldPlainSerializer: TypeAlias = (
  "core_schema.SerializerFunction | _Partial"
)
```

A field serializer method or function in `plain` mode.

## FieldWrapSerializer

```python
FieldWrapSerializer: TypeAlias = (
  "core_schema.WrapSerializerFunction | _Partial"
)
```

A field serializer method or function in `wrap` mode.

## FieldSerializer

```python
FieldSerializer: TypeAlias = (
  "FieldPlainSerializer | FieldWrapSerializer"
)
```

A field serializer method or function.

## ModelPlainSerializerWithInfo

```python
ModelPlainSerializerWithInfo: TypeAlias = Callable[
  [Any, SerializationInfo], Any
]
```

A model serializer method with the `info` argument, in `plain` mode.

## ModelPlainSerializerWithoutInfo

```python
ModelPlainSerializerWithoutInfo: TypeAlias = Callable[
  [Any], Any
]
```

A model serializer method without the `info` argument, in `plain` mode.

## ModelPlainSerializer

```python
ModelPlainSerializer: TypeAlias = (
  "ModelPlainSerializerWithInfo | ModelPlainSerializerWithoutInfo"
)
```

A model serializer method in `plain` mode.

## ModelWrapSerializerWithInfo

```python
ModelWrapSerializerWithInfo: TypeAlias = Callable[
  [Any, SerializerFunctionWrapHandler, SerializationInfo], Any
]
```

A model serializer method with the `info` argument, in `wrap` mode.

## ModelWrapSerializerWithoutInfo

```python
ModelWrapSerializerWithoutInfo: TypeAlias = Callable[
  [Any, SerializerFunctionWrapHandler], Any
]
```

A model serializer method without the `info` argument, in `wrap` mode.

## ModelWrapSerializer

```python
ModelWrapSerializer: TypeAlias = (
  "ModelWrapSerializerWithInfo | ModelWrapSerializerWithoutInfo"
)
```

A model serializer method in `wrap` mode.

## PlainSerializer

```python
PlainSerializer(
  func: SerializerFunction,
  return_type: Any = PydanticUndefined,
  when_used: WhenUsed = "always",
)
```

Plain serializers use a function to modify the output of serialization.

This is particularly helpful when you want to customize the serialization for annotated types. Consider an input of `list`, which will be serialized into a space-delimited string.

```python
from typing import List
from typing_extensions import Annotated
from pydantic import BaseModel, PlainSerializer

CustomStr = Annotated[
  List, PlainSerializer(lambda x: ' '.join(x), return_type=str)
]

class StudentModel(BaseModel):
  courses: CustomStr

student = StudentModel(courses=['Math', 'Chemistry', 'English'])
print(student.model_dump())
#> {'courses': 'Math Chemistry English'}
```

Attributes:

| Name          | Type                              | Description  |
|---------------|-----------------------------------|--------------|
| `func`       | `SerializerFunction`              | The serializer function. |
| `return_type`| `Any`                             | The return type for the function. If omitted it will be inferred from the type annotation. |
| `when_used`  | `WhenUsed`                        | Determines when this serializer should be used. Accepts a string with values 'always', 'unless-none', 'json', and 'json-unless-none'. Defaults to 'always'. |

## WrapSerializer

```python
WrapSerializer(
  func: WrapSerializerFunction,
  return_type: Any = PydanticUndefined,
  when_used: WhenUsed = "always",
)
```

Wrap serializers receive the raw inputs along with a handler function that applies the standard serialization logic, and can modify the resulting value before returning it as the final output of serialization.

For example, here's a scenario in which a wrap serializer transforms timezones to UTC **and** utilizes the existing `datetime` serialization logic.

```python
from datetime import datetime, timezone
from typing import Any, Dict
from typing_extensions import Annotated
from pydantic import BaseModel, WrapSerializer

class EventDatetime(BaseModel):
  start: datetime
  end: datetime

def convert_to_utc(value: Any, handler, info) -> Dict[str, datetime]:
  partial_result = handler(value, info)
  if info.mode == 'json':
    return {
      k: datetime.fromisoformat(v).astimezone(timezone.utc)
      for k, v in partial_result.items()
    }
  return {k: v.astimezone(timezone.utc) for k, v in partial_result.items()}

UTCEventDatetime = Annotated[EventDatetime, WrapSerializer(convert_to_utc)]

class EventModel(BaseModel):
  event_datetime: UTCEventDatetime

dt = EventDatetime(
  start='2024-01-01T07:00:00-08:00', end='2024-01-03T20:00:00+06:00'
)
event = EventModel(event_datetime=dt)
print(event.model_dump())
#> {'event_datetime': {'start': datetime.datetime(2024, 1, 1, 15, 0, tzinfo=datetime.timezone.utc), 'end': datetime.datetime(2024, 1, 3, 14, 0, tzinfo=datetime.timezone.utc)}}
print(event.model_dump_json())
#> {"event_datetime":{"start":"2024-01-01T15:00:00Z","end":"2024-01-03T14:00:00Z"}}
```

Attributes:

| Name          | Type                              | Description  |
|---------------|-----------------------------------|--------------|
| `func`       | `WrapSerializerFunction`          | The serializer function to be wrapped. |
| `return_type`| `Any`                             | The return type for the function. If omitted it will be inferred from the type annotation. |
| `when_used`  | `WhenUsed`                        | Determines when this serializer should be used. Accepts a string with values 'always', 'unless-none', 'json', and 'json-unless-none'. Defaults to 'always'. |

## field_serializer

```python
field_serializer(
  *fields: str,
  mode: Literal["plain", "wrap"] = "plain",
  return_type: Any = PydanticUndefined,
  when_used: WhenUsed = "always",
  check_fields: bool | None = None
) -> (
  Callable[[FieldWrapSerializerT], FieldWrapSerializerT]
  | Callable[[FieldPlainSerializerT], FieldPlainSerializerT]
)
```

Decorator that enables custom field serialization.

In the below example, a field of type `set` is used to mitigate duplication. A `field_serializer` is used to serialize the data as a sorted list.

```python
from typing import Set
from pydantic import BaseModel, field_serializer

class StudentModel(BaseModel):
  name: str = 'Jane'
  courses: Set[str]

  @field_serializer('courses', when_used='json')
  def serialize_courses_in_order(self, courses: Set[str]):
    return sorted(courses)

student = StudentModel(courses={'Math', 'Chemistry', 'English'})
print(student.model_dump_json())
#> {"name":"Jane","courses":["Chemistry","English","Math"]}
```

See [Custom serializers](https://docs.pydantic.dev/latest/concepts/serialization/#custom-serializers) for more information.

Four signatures are supported:

- `(self, value: Any, info: FieldSerializationInfo)`
- `(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)`
- `(value: Any, info: SerializationInfo)`
- `(value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

Parameters:

| Name          | Type                              | Description  | Default  |
|---------------|-----------------------------------|--------------|----------|
| `fields`     | `str`                             | Which field(s) the method should be called on. | `()` |
| `mode`       | `Literal['plain', 'wrap']`       | The serialization mode. | `'plain'` |
| `return_type`| `Any`                             | Optional return type for the function, if omitted it will be inferred from the type annotation. | `PydanticUndefined` |
| `when_used`  | `WhenUsed`                        | Determines the serializer will be used for serialization. | `'always'` |
| `check_fields`| `bool | None`                   | Whether to check that the fields actually exist on the model. | `None` |

Returns:

| Type          | Description  |
|---------------|--------------|
| `Callable[[FieldWrapSerializerT], FieldWrapSerializerT]` | The decorator function. |

## model_serializer

```python
model_serializer(
  f: (_ModelPlainSerializerT | _ModelWrapSerializerT | None = None,
  /,
  *,
  mode: Literal["plain", "wrap"] = "plain",
  when_used: WhenUsed = "always",
  return_type: Any = PydanticUndefined,
) -> (
  _ModelPlainSerializerT
  | Callable[[_ModelWrapSerializerT], _ModelWrapSerializerT]
  | Callable[[_ModelPlainSerializerT], _ModelPlainSerializerT]
)
```

Decorator that enables custom model serialization.

This is useful when a model need to be serialized in a customized manner, allowing for flexibility beyond just specific fields.

An example would be to serialize temperature to the same temperature scale, such as degrees Celsius.

```python
from typing import Literal
from pydantic import BaseModel, model_serializer

class TemperatureModel(BaseModel):
  unit: Literal['C', 'F']
  value: int

  @model_serializer()
  def serialize_model(self):
    if self.unit == 'F':
      return {'unit': 'C', 'value': int((self.value - 32) / 1.8)}
    return {'unit': self.unit, 'value': self.value}

temperature = TemperatureModel(unit='F', value=212)
print(temperature.model_dump())
#> {'unit': 'C', 'value': 100}
```

Two signatures are supported for `mode='plain'`, which is the default:

- `(self)`
- `(self, info: SerializationInfo)`

And two other signatures for `mode='wrap'`:

- `(self, nxt: SerializerFunctionWrapHandler)`
- `(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

See [Custom serializers](https://docs.pydantic.dev/latest/concepts/serialization/#custom-serializers) for more information.

Parameters:

| Name          | Type                              | Description  | Default  |
|---------------|-----------------------------------|--------------|----------|
| `f`          | `_ModelPlainSerializerT | _ModelWrapSerializerT | None` | The function to be decorated. | `None` |
| `mode`       | `Literal['plain', 'wrap']`       | The serialization mode. | `'plain'` |
| `when_used`  | `WhenUsed`                        | Determines when this serializer should be used. | `'always'` |
| `return_type`| `Any`                             | The return type for the function. If omitted it will be inferred from the type annotation. | `PydanticUndefined` |

Returns:

| Type          | Description  |
|---------------|--------------|
| `_ModelPlainSerializerT | Callable[[_ModelWrapSerializerT], _ModelWrapSerializerT] | Callable[[_ModelPlainSerializerT], _ModelPlainSerializerT]` | The decorator function.