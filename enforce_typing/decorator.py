import typing
import inspect

from wrapt import decorator
from contextlib import suppress
from functools import wraps
from typing import Any, Callable, TypeVar, Type, overload, Union, Literal


F = TypeVar("F", bound=Callable[..., Any])


def _check_types(spec: inspect.FullArgSpec, *args: Any, **kwargs: Any) -> None:
    params = dict(zip(spec.args, args))
    params.update(kwargs)

    for name, value in params.items():
        with suppress(KeyError):
            type_hint = spec.annotations[name]
            if isinstance(type_hint, typing._SpecialForm):
                continue
            actual_type = getattr(type_hint, "__origin__", type_hint)
            literal = actual_type is Literal
            actual_type = (
                type_hint.__args__
                if isinstance(actual_type, typing._SpecialForm)
                else actual_type
            )

            if literal:
                if value not in actual_type:
                    raise TypeError(
                        f"Expected type '{type_hint}' for attribute '{name}' but received value '{value}'"
                    )
            else:
                if not isinstance(value, actual_type):
                    raise TypeError(
                        f"Expected type '{type_hint}' for attribute '{name}' but received type '{type(value)}'"
                    )

@overload
def enforce_types(wrapped: F) -> F:
    ...


@overload
def enforce_types(wrapped: Type) -> Type:
    ...


def enforce_types(wrapped: Union[F, Type]) -> Union[F, Type]:
    spec = inspect.getfullargspec(wrapped)

    @decorator
    def wrap(_wrapped, instance, args, kwargs):
        if inspect.isclass(wrapped):
            _check_types(spec, instance, *args, **kwargs)
        else:
            _check_types(spec, *args, **kwargs)

        return _wrapped(*args, **kwargs)

    if inspect.isclass(wrapped):
        wrapped.__init__ = wrap(wrapped.__init__)  # type: ignore

        return wrapped

    return wrap(wrapped)
