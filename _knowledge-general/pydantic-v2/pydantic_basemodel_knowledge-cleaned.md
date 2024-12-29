# BaseModel

Pydantic models are simply classes which inherit from `BaseModel` and define fields as annotated attributes.

## pydantic.BaseModel

Usage Documentation

A base class for creating Pydantic models.

### Attributes:

| Name | Type | Description |
|---|---|---|
| `__class_vars__` | `set[str]` | The names of the class variables defined on the model. |
| `__private_attributes__` | `Dict[str, ModelPrivateAttr]` | Metadata about the private attributes of the model. |
| `__signature__` | `Signature` | The synthesized `__init__` `Signature` of the model. |
| `__pydantic_complete__` | `bool` | Whether model building is completed, or if there are still undefined fields. |
| `__pydantic_core_schema__` | `CoreSchema` | The core schema of the model. |
| `__pydantic_custom_init__` | `bool` | Whether the model has a custom `__init__` function. |
| `__pydantic_decorators__` | `DecoratorInfos` | Metadata containing the decorators defined on the model. |
| `__pydantic_generic_metadata__` | `PydanticGenericMetadata` | Metadata for generic models. |
| `__pydantic_parent_namespace__` | `Dict[str, Any] | None` | Parent namespace of the model. |
| `__pydantic_post_init__` | `None | Literal['model_post_init']` | The name of the post-init method for the model, if defined. |
| `__pydantic_root_model__` | `bool` | Whether the model is a `RootModel`. |
| `__pydantic_serializer__` | `SchemaSerializer` | The `pydantic-core` `SchemaSerializer` used to dump instances of the model. |
| `__pydantic_validator__` | `SchemaValidator | PluggableSchemaValidator` | The `pydantic-core` `SchemaValidator` used to validate instances of the model. |
| `__pydantic_fields__` | `Dict[str, FieldInfo]` | A dictionary of field names and their corresponding `FieldInfo` objects. |
| `__pydantic_computed_fields__` | `Dict[str, ComputedFieldInfo]` | A dictionary of computed field names and their corresponding `ComputedFieldInfo` objects. |
| `__pydantic_extra__` | `dict[str, Any] | None` | A dictionary containing extra values. |
| `__pydantic_fields_set__` | `set[str]` | The names of fields explicitly set during instantiation. |
| `__pydantic_private__` | `dict[str, Any] | None` | Values of private attributes set on the model instance. |

### Source code in `pydantic/main.py`

```python
class BaseModel(metaclass=_model_construction.ModelMetaclass):
    """Usage docs: https://docs.pydantic.dev/2.10/concepts/models/
    A base class for creating Pydantic models.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict()
    __class_vars__: ClassVar[set[str]]
    __private_attributes__: ClassVar[Dict[str, ModelPrivateAttr]]
    __signature__: ClassVar[Signature]
    __pydantic_complete__: ClassVar[bool] = False
    __pydantic_core_schema__: ClassVar[CoreSchema]
    __pydantic_custom_init__: ClassVar[bool]
    __pydantic_decorators__: ClassVar[_decorators.DecoratorInfos] = _decorators.DecoratorInfos()
    __pydantic_generic_metadata__: ClassVar[_generics.PydanticGenericMetadata]
    __pydantic_parent_namespace__: ClassVar[Dict[str, Any] | None] = None
    __pydantic_post_init__: ClassVar[None | Literal['model_post_init']]
    __pydantic_root_model__: ClassVar[bool] = False
    __pydantic_serializer__: ClassVar[SchemaSerializer]
    __pydantic_validator__: ClassVar[SchemaValidator | PluggableSchemaValidator]
    __pydantic_fields__: ClassVar[Dict[str, FieldInfo]]
    __pydantic_computed_fields__: ClassVar[Dict[str, ComputedFieldInfo]]
    __pydantic_extra__: dict[str, Any] | None = _model_construction.NoInitField(init=False)
    __pydantic_fields_set__: set[str] = _model_construction.NoInitField(init=False)
    __pydantic_private__: dict[str, Any] | None = _model_construction.NoInitField(init=False)

    def __init__(self, /, **data: Any) -> None:
        """Create a new model by parsing and validating input data from keyword arguments."
        validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
        if self is not validated_self:
            warnings.warn(
                'A custom validator is returning a value other than `self`.
                "Returning anything other than `self` from a top level model validator isn't supported when validating via `__init__`."
                'See the `model_validator` docs for more details.',
                stacklevel=2,
            )

    @classmethod
    def model_construct(cls, _fields_set: set[str] | None = None, **values: Any) -> Self:
        """Creates a new instance of the `Model` class with validated data."
        m = cls.__new__(cls)
        fields_values: dict[str, Any] = {}
        fields_set = set()
        for name, field in cls.__pydantic_fields__.items():
            if field.alias is not None and field.alias in values:
                fields_values[name] = values.pop(field.alias)
                fields_set.add(name)
        # Additional logic omitted for brevity
        return m
```

### model_copy

```python
def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
    """Returns a copy of the model."
    copied = self.__deepcopy__() if deep else self.__copy__()
    if update:
        if self.model_config.get('extra') == 'allow':
            for k, v in update.items():
                if k in self.__pydantic_fields__:
                    copied.__dict__[k] = v
                else:
                    if copied.__pydantic_extra__ is None:
                        copied.__pydantic_extra__ = {}
                    copied.__pydantic_extra__[k] = v
        else:
            copied.__dict__.update(update)
        copied.__pydantic_fields_set__.update(update.keys())
    return copied
```

### model_dump

```python
def model_dump(self, *, mode: Literal['json', 'python'] | str = 'python', include: IncEx | None = None, exclude: IncEx | None = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool | Literal['none', 'warn', 'error'] = True, serialize_as_any: bool = False) -> dict[str, Any]:
    """Generate a dictionary representation of the model."
    return self.__pydantic_serializer__.to_python(
        self,
        mode=mode,
        by_alias=by_alias,
        include=include,
        exclude=exclude,
        context=context,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        serialize_as_any=serialize_as_any,
    )
```

### model_dump_json

```python
def model_dump_json(self, *, indent: int | None = None, include: IncEx | None = None, exclude: IncEx | None = None, context: Any | None = None, by_alias: bool = False, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, round_trip: bool = False, warnings: bool | Literal['none', 'warn', 'error'] = True, serialize_as_any: bool = False) -> str:
    """Generates a JSON representation of the model."
    return self.__pydantic_serializer__.to_json(
        self,
        indent=indent,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        serialize_as_any=serialize_as_any,
    ).decode()
```

### model_json_schema

```python
def model_json_schema(cls, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE, schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema, mode: JsonSchemaMode = 'validation') -> dict[str, Any]:
    """Generates a JSON schema for a model class."
    return model_json_schema(
        cls, by_alias=by_alias, ref_template=ref_template, schema_generator=schema_generator, mode=mode
    )
```

### model_validate

```python
def model_validate(cls, obj: Any, *, strict: bool | None = None, from_attributes: bool | None = None, context: Any | None = None) -> Self:
    """Validate a pydantic model instance."
    return cls.__pydantic_validator__.validate_python(
        obj, strict=strict, from_attributes=from_attributes, context=context
    )
```

### model_validate_json

```python
def model_validate_json(cls, json_data: str | bytes | bytearray, *, strict: bool | None = None, context: Any | None = None) -> Self:
    """Validate the given JSON data against the Pydantic model."
    return cls.__pydantic_validator__.validate_json(json_data, strict=strict, context=context)
```

### model_validate_strings

```python
def model_validate_strings(cls, obj: Any, *, strict: bool | None = None, context: Any | None = None) -> Self:
    """Validate the given object with string data against the Pydantic model."
    return cls.__pydantic_validator__.validate_strings(obj, strict=strict, context=context)
```

### copy

```python
def copy(self, *, include: AbstractSetIntStr | MappingIntStrAny | None = None, exclude: AbstractSetIntStr | MappingIntStrAny | None = None, update: Dict[str, Any] | None = None, deep: bool = False) -> Self:
    """Returns a copy of the model."
    return self.model_copy(update=update, deep=deep)
```

### create_model

```python
def create_model(model_name: str, /, *, __config__: ConfigDict | None = None, __doc__: str | None = None, __base__: type[ModelT] | tuple[type[ModelT], ...] | None = None, __module__: str | None = None, __validators__: dict[str, Callable[..., Any]] | None = None, __cls_kwargs__: dict[str, Any] | None = None, **field_definitions: Any) -> type[ModelT]:
    """Dynamically creates and returns a new Pydantic model."
    # Implementation omitted for brevity
```

