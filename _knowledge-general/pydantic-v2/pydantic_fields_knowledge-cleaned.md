## Fields

In this section, we will go through the available mechanisms to customize Pydantic model fields: default values, JSON Schema metadata, constraints, etc.

To do so, the `Field()` function is used a lot, and behaves the same way as the standard library `field()` function for dataclasses:

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    name: str = Field(frozen=True)
```

### Note
Even though `name` is assigned a value, it is still required and has no default value. If you want to emphasize on the fact that a value must be provided, you can use the [ellipsis](https://docs.python.org/3/library/constants.html#Ellipsis):

```python
class Model(BaseModel):
    name: str = Field(..., frozen=True)
```

However, its usage is discouraged as it doesn't play well with static type checkers.

### The annotated pattern
To apply constraints or attach `Field()` functions to a model field, Pydantic supports the `Annotated` typing construct to attach metadata to an annotation:

```python
from typing_extensions import Annotated
from pydantic import BaseModel, Field, WithJsonSchema

class Model(BaseModel):
    name: Annotated[str, Field(strict=True), WithJsonSchema({'extra': 'data'})]
```

As far as static type checkers are concerned, `name` is still typed as `str`, but Pydantic leverages the available metadata to add validation logic, type constraints, etc.

Using this pattern has some advantages:

- Using the `f: <type> = Field(...)` form can be confusing and might trick users into thinking `f` has a default value, while in reality it is still required.
- You can provide an arbitrary amount of metadata elements for a field. As shown in the example above, the `Field()` function only supports a limited set of constraints/metadata, and you may have to use different Pydantic utilities such as `WithJsonSchema` in some cases.
- Types can be made reusable.

However, note that certain arguments to the `Field()` function (namely, `default`, `default_factory`, and `alias`) are taken into account by static type checkers to synthesize a correct `__init__` method. The annotated pattern is _not_ understood by them, so you should use the normal assignment form instead.

### Default values
The `default` parameter is used to define a default value for a field.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(default='John Doe')

user = User()
print(user)
#> name='John Doe'
```

### Note
If you use the `Optional` annotation, it doesn't mean that the field has a default value of `None`!

You can also use `default_factory` (but not both at the same time) to define a callable that will be called to generate a default value.

```python
from uuid import uuid4
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

The default factory can also take a single required argument, in which the case the already validated data will be passed as a dictionary.

```python
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])

user = User(email='user@example.com')
print(user.username)
#> user@example.com
```

### Validate default values
By default, Pydantic will _not_ validate default values. The `validate_default` field parameter (or the `validate_default` configuration value) can be used to enable this behavior:

```python
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)

try:
    user = User()
except ValidationError as e:
    print(e)
# 1 validation error for User
# age
# Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
```

### Mutable default values
A common source of bugs in Python is to use a mutable object as a default value for a function or method argument, as the same instance ends up being reused in each call.

While the same thing can be done in Pydantic, it is not required. In the event that the default value is not hashable, Pydantic will create a deep copy of the default value when creating each instance of the model:

```python
from typing import Dict, List
from pydantic import BaseModel

class Model(BaseModel):
    item_counts: List[Dict[str, int]] = [{}]

m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]
m2 = Model()
print(m2.item_counts)
#> [{}]
```

### Field aliases
For validation and serialization, you can define an alias for a field. There are three ways to define an alias:

- `Field(alias='foo')`
- `Field(validation_alias='foo')`
- `Field(serialization_alias='foo')`

The `alias` parameter is used for both validation and serialization. If you want to use different aliases for validation and serialization respectively, you can use the `validation_alias` and `serialization_alias` parameters.

Here is an example of using the `alias` parameter:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(alias='username')

user = User(username='johndoe')
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))
#> {'username': 'johndoe'}
```

### Numeric Constraints
There are some keyword arguments that can be used to constrain numeric values:

- `gt` - greater than
- `lt` - less than
- `ge` - greater than or equal to
- `le` - less than or equal to
- `multiple_of` - a multiple of the given number
- `allow_inf_nan` - allow `'inf'`, `'-inf'`, `'nan'` values

Here's an example:

```python
from pydantic import BaseModel, Field

class Foo(BaseModel):
    positive: int = Field(gt=0)
    non_negative: int = Field(ge=0)
    negative: int = Field(lt=0)
    non_positive: int = Field(le=0)
    even: int = Field(multiple_of=2)
    love_for_pydantic: float = Field(allow_inf_nan=True)

foo = Foo(
    positive=1,
    non_negative=0,
    negative=-1,
    non_positive=0,
    even=2,
    love_for_pydantic=float('inf'),
)
print(foo)
# positive=1 non_negative=0 negative=-1 non_positive=0 even=2 love_for_pydantic=inf
```

### String Constraints
There are fields that can be used to constrain strings:

- `min_length`: Minimum length of the string.
- `max_length`: Maximum length of the string.
- `pattern`: A regular expression that the string must match.

Here's an example:

```python
from pydantic import BaseModel, Field

class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\\d*$')

foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
#> short='foo' long='foobarbaz' regex='123'
```

### Decimal Constraints
There are fields that can be used to constrain decimals:

- `max_digits`: Maximum number of digits within the `Decimal`. It does not include a zero before the decimal point or trailing decimal zeroes.
- `decimal_places`: Maximum number of decimal places allowed. It does not include trailing decimal zeroes.

Here's an example:

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)

foo = Foo(precise=Decimal('123.45'))
print(foo)
#> precise=Decimal('123.45')
```

### Field Representation
The parameter `repr` can be used to control whether the field should be included in the string representation of the model.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(repr=True)
    age: int = Field(repr=False)

user = User(name='John', age=42)
print(user)
#> name='John'
```

### Exclude
The `exclude` parameter can be used to control which fields should be excluded from the model when exporting the model.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(exclude=True)

user = User(name='John', age=42)
print(user.model_dump())
#> {'name': 'John'}
```