## JSON

### Json Parsing

Pydantic provides builtin JSON parsing, which helps achieve:

- Significant performance improvements without the cost of using a 3rd party library
- Support for custom errors
- Support for `strict` specifications

Here's an example of Pydantic's builtin JSON parsing via the `model_validate_json` method, showcasing the support for `strict` specifications while parsing JSON data that doesn't match the model's type annotations:

```python
from datetime import date
from typing import Tuple
from pydantic import BaseModel, ConfigDict, ValidationError

class Event(BaseModel):
    model_config = ConfigDict(strict=True)
    when: date
    where: Tuple[int, int]

json_data = '{"when": "1987-01-28", "where": [51, -1]}'
print(Event.model_validate_json(json_data))
#> when=datetime.date(1987, 1, 28) where=(51, -1)
try:
    Event.model_validate({'when': '1987-01-28', 'where': [51, -1]})
except ValidationError as e:
    print(e)
    """
    2 validation errors for Event
    when
     Input should be a valid date [type=date_type, input_value='1987-01-28', input_type=str]
    where
     Input should be a valid tuple [type=tuple_type, input_value=[51, -1], input_type=list]
    """
```

1. JSON has no `date` or tuple types, but Pydantic knows that so allows strings and arrays as inputs respectively when parsing JSON directly.
2. If you pass the same values to the `model_validate` method, Pydantic will raise a validation error because the `strict` configuration is enabled.

In v2.5.0 and above, Pydantic uses `jiter`, a fast and iterable JSON parser, to parse JSON data. Using `jiter` compared to `serde` results in modest performance improvements that will get even better in the future.

The `jiter` JSON parser is almost entirely compatible with the `serde` JSON parser, with one noticeable enhancement being that `jiter` supports deserialization of `inf` and `NaN` values. In the future, `jiter` is intended to enable support validation errors to include the location in the original JSON input which contained the invalid value.

### Partial JSON Parsing

**Starting in v2.7.0**, Pydantic's JSON parser offers support for partial JSON parsing, which is exposed via `pydantic_core.from_json`. Here's an example of this feature in action:

```python
from pydantic_core import from_json
partial_json_data = '["aa", "bb", "c'
try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as e:
    print(e)
    #> EOF while parsing a string at line 1 column 15
result = from_json(partial_json_data, allow_partial=True)
print(result)
#> ['aa', 'bb']
```

This also works for deserializing partial dictionaries. For example:

```python
from pydantic_core import from_json
partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

Validating LLM Output

This feature is particularly beneficial for validating LLM outputs. We've written some blog posts about this topic, which you can find [here](https://pydantic.dev/articles).

In future versions of Pydantic, we expect to expand support for this feature through either Pydantic's other JSON validation functions or model configuration. Stay tuned 🚀!

For now, you can use `pydantic_core.from_json` in combination with `pydantic.main.BaseModel.model_validate` to achieve the same result. Here's an example:

```python
from pydantic_core import from_json
from pydantic import BaseModel

class Dog(BaseModel):
    breed: str
    name: str
    friends: list

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog = Dog.model_validate(from_json(partial_dog_json, allow_partial=True))
print(repr(dog))
#> Dog(breed='lab', name='fluffy', friends=['buddy', 'spot', 'rufus'])
```

Tip

For partial JSON parsing to work reliably, all fields on the model should have default values.

Check out the following example for a more in-depth look at how to use default values with partial JSON parsing:

```python
from typing import Any, Optional, Tuple
import pydantic_core
from typing_extensions import Annotated
from pydantic import BaseModel, ValidationError, WrapValidator

def default_on_error(v, handler) -> Any:
    """
    Raise a PydanticUseDefault exception if the value is missing.
    This is useful for avoiding errors from partial
    JSON preventing successful validation.
    """
    try:
        return handler(v)
    except ValidationError as exc:
        if all(e['type'] == 'missing' for e in exc.errors()):
            raise pydantic_core.PydanticUseDefault()
        else:
            raise

class NestedModel(BaseModel):
    x: int
    y: str

class MyModel(BaseModel):
    foo: Optional[str] = None
    bar: Annotated[
        Optional[Tuple[str, int]], WrapValidator(default_on_error)
    ] = None
    nested: Annotated[
        Optional[NestedModel], WrapValidator(default_on_error)
    ] = None

m = MyModel.model_validate(
    pydantic_core.from_json('{"foo": "x", "bar": ["world",', allow_partial=True)
)
print(repr(m))
#> MyModel(foo='x', bar=None, nested=None)

m = MyModel.model_validate(
    pydantic_core.from_json(
        '{"foo": "x", "bar": ["world", 1], "nested": {"x":', allow_partial=True
    )
)
print(repr(m))
#> MyModel(foo='x', bar=('world', 1), nested=None)
```

### Caching Strings

**Starting in v2.7.0**, Pydantic's JSON parser offers support for configuring how Python strings are cached during JSON parsing and validation. The `cache_strings` setting can take any of the following values:

- `True` or `'all'` (the default): cache all strings
- `'keys'`: cache only dictionary keys
- `False` or `'none'`: no caching

Using the string caching feature results in performance improvements, but increases memory usage slightly.

### JSON Serialization

For more information on JSON serialization, see the [Serialization Concepts](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump_json) page.