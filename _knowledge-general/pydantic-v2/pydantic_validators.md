## Validators

In addition to Pydantic's [built-in validation capabilities](https://docs.pydantic.dev/latest/concepts/fields/#field-constraints), you can leverage custom validators at the field and model levels to enforce more complex constraints and ensure the integrity of your data.

### Field validators

API Documentation

`pydantic.functional_validators.WrapValidator` `pydantic.functional_validators.PlainValidator` `pydantic.functional_validators.BeforeValidator` `pydantic.functional_validators.AfterValidator` `pydantic.functional_validators.field_validator`

In its simplest form, a field validator is a callable taking the value to be validated as an argument and **returning the validated value**. The callable can perform checks for specific conditions (see [raising validation errors](https://docs.pydantic.dev/latest/concepts/validators/#raising-validation-errors)) and make changes to the validated value (coercion or mutation).

**Four** different types of validators can be used. They can all be defined using the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) or using the `field_validator()` decorator, applied on a class method:

- **_After_ validators**: run after Pydantic's internal validation. They are generally more type safe and thus easier to implement.

Here is an example of a validator performing a validation check, and returning the value unchanged.

```python
from typing_extensions import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError

def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value

class Model(BaseModel):
    number: Annotated[int, AfterValidator(is_even)]

try:
    Model(number=1)
except ValidationError as err:
    print(err)
# 1 validation error for Model
# number
#  Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
```  

Here is an example of a validator performing a validation check, and returning the value unchanged, this time using the `field_validator()` decorator.

```python
from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    number: int
    @field_validator('number', mode='after')
    @classmethod
    def is_even(cls, value: int) -> int:
        if value % 2 == 1:
            raise ValueError(f'{value} is not an even number')
        return value

try:
    Model(number=1)
except ValidationError as err:
    print(err)
# 1 validation error for Model
# number
#  Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
```  

Example mutating the value

Here is an example of a validator making changes to the validated value (no exception is raised).

```python
from typing_extensions import Annotated
from pydantic import AfterValidator, BaseModel

def double_number(value: int) -> int:
    return value * 2

class Model(BaseModel):
    number: Annotated[int, AfterValidator(double_number)]

print(Model(number=2))
#> number=4
```  

```python
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    number: int
    @field_validator('number', mode='after')
    @classmethod
    def double_number(cls, value: int) -> int:
        return value * 2

print(Model(number=2))
#> number=4
```  

- **_Before_ validators**: run before Pydantic's internal parsing and validation (e.g. coercion of a `str` to an `int`). These are more flexible than _after_ validators, but they also have to deal with the raw input, which in theory could be any arbitrary object. The value returned from this callable is then validated against the provided type annotation by Pydantic.

```python
from typing import Any, List
from typing_extensions import Annotated
from pydantic import BaseModel, BeforeValidator, ValidationError

def ensure_list(value: Any) -> Any:
    if not isinstance(value, list):
        return [value]
    else:
        return value

class Model(BaseModel):
    numbers: Annotated[List[int], BeforeValidator(ensure_list)]

print(Model(numbers=2))
#> numbers=[2]
try:
    Model(numbers='str')
except ValidationError as err:
    print(err)
# 1 validation error for Model
# numbers.0
#  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
```  

```python
from typing import Any, List
from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    numbers: List[int]
    @field_validator('numbers', mode='before')
    @classmethod
    def ensure_list(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return [value]
        else:
            return value

print(Model(numbers=2))
#> numbers=[2]
try:
    Model(numbers='str')
except ValidationError as err:
    print(err)
# 1 validation error for Model
# numbers.0
#  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
```  

- **_Plain_ validators**: act similarly to _before_ validators but they terminate validation immediately after returning, so no further validators are called and Pydantic does not do any of its internal validation against the field type.

```python
from typing import Any
from typing_extensions import Annotated
from pydantic import BaseModel, PlainValidator

def val_number(value: Any) -> Any:
    if isinstance(value, int):
        return value * 2
    else:
        return value

class Model(BaseModel):
    number: Annotated[int, PlainValidator(val_number)]

print(Model(number=4))
#> number=8
print(Model(number='invalid'))
#> number='invalid'
```  

```python
from typing import Any
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    number: int
    @field_validator('number', mode='plain')
    @classmethod
    def val_number(cls, value: Any) -> Any:
        if isinstance(value, int):
            return value * 2
        else:
            return value

print(Model(number=4))
#> number=8
print(Model(number='invalid'))
#> number='invalid'
```  

- **_Wrap_ validators**: are the most flexible of all. You can run code before or after Pydantic and other validators process the input, or you can terminate validation immediately, either by returning the value early or by raising an error.

```python
from typing import Any
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, WrapValidator

def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
    try:
        return handler(value)
    except ValidationError as err:
        if err.errors()[0]['type'] == 'string_too_long':
            return handler(value[:5])
        else:
            raise

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]

print(Model(my_string='abcde'))
#> my_string='abcde'
print(Model(my_string='abcdef'))
#> my_string='abcde'
```  

```python
from typing import Any
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, field_validator

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5)]
    @field_validator('my_string', mode='wrap')
    @classmethod
    def truncate(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> str:
        try:
            return handler(value)
        except ValidationError as err:
            if err.errors()[0]['type'] == 'string_too_long':
                return handler(value[:5])
            else:
                raise

print(Model(my_string='abcde'))
#> my_string='abcde'
print(Model(my_string='abcdef'))
#> my_string='abcde'
```  

### Model validators

Validation can also be performed on the entire model's data using the `model_validator()` decorator.

**Three** different types of model validators can be used:

- **_After_ validators**: run after the whole model has been validated. As such, they are defined as instance methods and can be seen as post-initialization hooks. Important note: the validated instance should be returned.

```python
from typing_extensions import Self
from pydantic import BaseModel, model_validator

class UserModel(BaseModel):
    username: str
    password: str
    password_repeat: str
    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError('Passwords do not match')
        return self
```  

- **_Before_ validators**: are run before the model is instantiated. These are more flexible than _after_ validators, but they also have to deal with the raw input, which in theory could be any arbitrary object.

```python
from typing import Any
from pydantic import BaseModel, model_validator

class UserModel(BaseModel):
    username: str
    @model_validator(mode='before')
    @classmethod
    def check_card_number_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'card_number' in data:
                raise ValueError("'card_number' should not be included")
        return data
```  

- **_Wrap_ validators**: are the most flexible of all. You can run code before or after Pydantic and other validators process the input data, or you can terminate validation immediately, either by returning the data early or by raising an error.

```python
import logging
from typing import Any
from typing_extensions import Self
from pydantic import BaseModel, ModelWrapValidatorHandler, ValidationError, model_validator

class UserModel(BaseModel):
    username: str
    @model_validator(mode='wrap')
    @classmethod
    def log_failed_validation(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        try:
            return handler(data)
        except ValidationError:
            logging.error('Model %s failed to validate with data %s', cls, data)
            raise
```  

### Raising validation errors

To raise a validation error, three types of exceptions can be used:

- `ValueError`: this is the most common exception raised inside validators.
- `AssertionError`: using the assert statement also works, but be aware that these statements are skipped when Python is run with the -O optimization flag.
- `PydanticCustomError`: a bit more verbose, but provides extra flexibility:

```python
from pydantic_core import PydanticCustomError
from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    x: int
    @field_validator('x', mode='after')
    @classmethod
    def validate_x(cls, v: int) -> int:
        if v % 42 == 0:
            raise PydanticCustomError(
                'the_answer_error',
                '{number} is the answer!',
                {'number': v},
            )
        return v

try:
    Model(x=42 * 2)
except ValidationError as e:
    print(e)
# 1 validation error for Model
# x
#  84 is the answer! [type=the_answer_error, input_value=84, input_type=int]
```  

### Validation info

Both the field and model validators callables (in all modes) can optionally take an extra `ValidationInfo` argument, providing useful extra information, such as:

- already validated data
- user defined context
- the current validation mode: either 'python' or 'json'
- the current field name

### Validation data

For field validators, the already validated data can be accessed using the `data` property. Here is an example than can be used as an alternative to the _after_ model validator example:

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class UserModel(BaseModel):
    password: str
    password_repeat: str
    username: str
    @field_validator('password_repeat', mode='after')
    @classmethod
    def check_passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data['password']:
            raise ValueError('Passwords do not match')
        return value
```  

### Validation context

You can pass a context object to the validation methods, which can be accessed inside the validator functions using the `context` property:

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class Model(BaseModel):
    text: str
    @field_validator('text', mode='after')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v

data = {'text': 'This is an example document'}
print(Model.model_validate(data)) # no context
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
```  

### Ordering of validators

When using the annotated pattern, the order in which validators are applied is defined as follows: _before_ and _wrap_ validators are run from right to left, and _after_ validators are then run from left to right:

```python
from pydantic import AfterValidator, BaseModel, BeforeValidator, WrapValidator

class Model(BaseModel):
    name: Annotated[
        str,
        AfterValidator(runs_3rd),
        AfterValidator(runs_4th),
        BeforeValidator(runs_2nd),
        WrapValidator(runs_1st),
    ]
```  

### Special types

Pydantic provides a few special utilities that can be used to customize validation.

- `InstanceOf` can be used to validate that a value is an instance of a given class.

```python
from typing import List
from pydantic import BaseModel, InstanceOf, ValidationError

class Fruit:
    def __repr__(self):
        return self.__class__.__name__

class Banana(Fruit): ...

class Apple(Fruit): ...

class Basket(BaseModel):
    fruits: List[InstanceOf[Fruit]]

print(Basket(fruits=[Banana(), Apple()]))
#> fruits=[Banana, Apple]
try:
    Basket(fruits=[Banana(), 'Apple'])
except ValidationError as e:
    print(e)
# 1 validation error for Basket
# fruits.1
#  Input should be an instance of Fruit [type=is_instance_of, input_value='Apple', input_type=str]
```  

- `SkipValidation` can be used to skip validation on a field.

```python
from typing import List
from pydantic import BaseModel, SkipValidation

class Model(BaseModel):
    names: List[SkipValidation[str]]

m = Model(names=['foo', 'bar'])
print(m)
#> names=['foo', 'bar']
m = Model(names=['foo', 123])
print(m)
#> names=['foo', 123]
```  

- `PydanticUseDefault` can be used to notify Pydantic that the default value should be used.

```python
from typing import Any
from pydantic_core import PydanticUseDefault
from typing_extensions import Annotated
from pydantic import BaseModel, BeforeValidator

def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value

class Model(BaseModel):
    name: Annotated[str, BeforeValidator(default_if_none)] = 'default_name'

print(Model(name=None))
#> name='default_name'
```  

### JSON Schema and field validators

When using _before_, _plain_ or _wrap_ field validators, the accepted input type may be different from the field annotation.

Consider the following example:

```python
from typing import Any
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    value: str
    @field_validator('value', mode='before')
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value

print(Model(value='a'))
#> value='a'
print(Model(value=1))
#> value='1'
```  

While the type hint for `value` is `str`, the `cast_ints` validator also allows integers. To specify the correct input type, the `json_schema_input_type` argument can be provided:

```python
from typing import Any, Union
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    value: str
    @field_validator(
        'value', mode='before', json_schema_input_type=Union[int, str]
    )
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value

print(Model.model_json_schema()['properties']['value'])
#> {'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'title': 'Value'}
```