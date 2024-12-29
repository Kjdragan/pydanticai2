# TypeAdapter

Type adapters provide a flexible way to perform validation and serialization based on a Python type.

A `TypeAdapter` instance exposes some of the functionality from `BaseModel` instance methods for types that do not have such methods (such as dataclasses, primitive types, and more).

**Note:** `TypeAdapter` instances are not types, and cannot be used as type annotations for fields.

## Parameters:

| Name            | Type                                                                 | Description                                                                                                                                                                                                                                                                                                                                                     | Default |
|-----------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| `type`          | `Any`                                                               | The type associated with the `TypeAdapter`.                                                                                                                                                                                                                                                                                                                                                                              | _required_ |
| `config`        | `ConfigDict` | Configuration for the `TypeAdapter`, should be a dictionary conforming to `ConfigDict`. Note You cannot provide a configuration when instantiating a `TypeAdapter` if the type you're using has its own config that cannot be overridden (ex: `BaseModel`, `TypedDict`, and `dataclass`). A `type-adapter-config-unused` error will be raised in this case. | `None`  |
| `_parent_depth` | `int`                                                               | Depth at which to search for the [parent frame](https://docs.python.org/3/reference/datamodel.html#frame-objects). This frame is used when resolving forward annotations during schema building, by looking for the globals and locals of this frame. Defaults to 2, which will result in the frame where the `TypeAdapter` was instantiated. Note This parameter is named with an underscore to suggest its private nature and discourage use. It may be deprecated in a minor version, so we only recommend using it if you're comfortable with potential change in behavior/support. It's default value is 2 because internally, the `TypeAdapter` class makes another call to fetch the frame. | `2`    |
| `module`        | `str`                                                               | The module that passes to plugin if provided.                                                                                                                                                                                                                                                                                                                                                                           | `None`  |

## Attributes:

| Name                | Type                               | Description                                                                                      |
|---------------------|------------------------------------|--------------------------------------------------------------------------------------------------|
| `core_schema`       | `CoreSchema`                       | The core schema for the type.                                                                    |
| `validator`         | `SchemaValidator`                  | The schema validator for the type.                                                               |
| `serializer`        | `SchemaSerializer`                 | The schema serializer for the type.                                                              |
| `pydantic_complete` | `bool`                             | Whether the core schema for the type is successfully built.                                     |

## Compatibility with `mypy`

Depending on the type used, `mypy` might raise an error when instantiating a `TypeAdapter`. As a workaround, you can explicitly annotate your variable:

```python
from typing import Union
from pydantic import TypeAdapter

ta: TypeAdapter[Union[str, int]] = TypeAdapter(Union[str, int]) # type: ignore[arg-type]
```

## Namespace management nuances and implementation details

Here, we collect some notes on namespace management, and subtle differences from `BaseModel`:

`BaseModel` uses its own `__module__` to find out where it was defined and then looks for symbols to resolve forward references in those globals. On the other hand, `TypeAdapter` can be initialized with arbitrary objects, which may not be types and thus do not have a `__module__` available. So instead we look at the globals in our parent stack frame.

It is expected that the `ns_resolver` passed to this function will have the correct namespace for the type we're adapting. See the source code for `TypeAdapter.__init__` and `TypeAdapter.rebuild` for various ways to construct this namespace.

This works for the case where this function is called in a module that has the target of forward references in its scope, but does not always work for more complex cases.

For example, take the following:

a.py
```python
from typing import Dict, List
IntList = List[int]
OuterDict = Dict[str, 'IntList']
```

b.py
```python
from a import OuterDict
from pydantic import TypeAdapter
IntList = int # replaces the symbol the forward reference is looking for
v = TypeAdapter(OuterDict)
v({'x': 1}) # should fail but doesn't
```

If `OuterDict` were a `BaseModel`, this would work because it would resolve the forward reference within the `a.py` namespace. But `TypeAdapter(OuterDict)` can't determine what module `OuterDict` came from.

In other words, the assumption that _all_ forward references exist in the module we are being called from is not technically always true. Although most of the time it is and it works fine for recursive models and such, `BaseModel`'s behavior isn't perfect either and _can_ break in similar ways, so there is no right or wrong between the two.

But at the very least this behavior is _subtly_ different from `BaseModel`'s.

## Source code in `pydantic/type_adapter.py`

```python
class TypeAdapter:
    def __init__(self, type: Any, *, config: ConfigDict | None = None, _parent_depth: int = 2, module: str | None = None) -> None:
        if _type_has_config(type) and config is not None:
            raise PydanticUserError(
                'Cannot use `config` when the type is a BaseModel, dataclass or TypedDict.'
                ' These types can have their own config and setting the config via the `config`
                ' parameter to TypeAdapter will not override it, thus the `config` you passed to'
                ' TypeAdapter becomes meaningless, which is probably not what you want.',
                code='type-adapter-config-unused',
            )
        self._type = type
        self._config = config
        self._parent_depth = _parent_depth
        self.pydantic_complete = False
        parent_frame = self._fetch_parent_frame()
        if parent_frame is not None:
            globalns = parent_frame.f_globals
            localns = parent_frame.f_locals if parent_frame.f_locals is not globalns else {}
        else:
            globalns = {}
            localns = {}
        self._module_name = module or cast(str, globalns.get('__name__', ''))
        self._init_core_attrs(
            ns_resolver=_namespace_utils.NsResolver(
                namespaces_tuple=_namespace_utils.NamespacesTuple(locals=localns, globals=globalns),
                parent_namespace=localns,
            ),
            force=False,
        )
```

## Methods

### rebuild

```python
rebuild(
    *,
    force: bool = False,
    raise_errors: bool = True,
    _parent_namespace_depth: int = 2,
    _types_namespace: MappingNamespace | None = None
) -> bool | None
```

Try to rebuild the pydantic-core schema for the adapter's type.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during the initial attempt to build the schema, and automatic rebuilding fails.

### validate_python

```python
validate_python(
    object: Any,
    /,
    *,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    context: dict[str, Any] | None = None,
    experimental_allow_partial: (bool | Literal['off', 'on', 'trailing-strings']) = False,
) -> T
```

Validate a Python object against the model.

### validate_json

```python
validate_json(
    data: str | bytes | bytearray,
    /,
    *,
    strict: bool | None = None,
    context: dict[str, Any] | None = None,
    experimental_allow_partial: (bool | Literal['off', 'on', 'trailing-strings']) = False,
) -> T
```

Validate a JSON string or bytes against the model.

### validate_strings

```python
validate_strings(
    obj: Any,
    /,
    *,
    strict: bool | None = None,
    context: dict[str, Any] | None = None,
    experimental_allow_partial: (bool | Literal['off', 'on', 'trailing-strings']) = False,
) -> T
```

Validate object contains string data against the model.

### get_default_value

```python
get_default_value(
    *,
    strict: bool | None = None,
    context: dict[str, Any] | None = None
) -> Some[T] | None
```

Get the default value for the wrapped type.

### dump_python

```python
dump_python(
    instance: T,
    /,
    *,
    mode: Literal['json', 'python'] = 'python',
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    by_alias: bool = False,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: (bool | Literal['none', 'warn', 'error']) = True,
    serialize_as_any: bool = False,
    context: dict[str, Any] | None = None,
) -> Any
```

Dump an instance of the adapted type to a Python object.

### dump_json

```python
dump_json(
    instance: T,
    /,
    *,
    indent: int | None = None,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    by_alias: bool = False,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: (bool | Literal['none', 'warn', 'error']) = True,
    serialize_as_any: bool = False,
    context: dict[str, Any] | None = None,
) -> bytes
```

Serialize an instance of the adapted type to JSON.

### json_schema

```python
json_schema(
    *,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    mode: JsonSchemaMode = 'validation'
) -> dict[str, Any]
```

Generate a JSON schema for the adapted type.

### json_schemas `staticmethod`

```python
json_schemas(
    inputs: Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]],
    /,
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]
```

Generate a JSON schema including definitions from multiple type adapters.