"""Decorator functions."""

from functools import wraps
from typing import Any, Callable, Type

from flask import request

from hisfs import File

from previewlib.messages import UNAUTHORIZED
from previewlib.orm import PreviewToken


__all__ = ['preview', 'file_preview']


def preview(token_class: Type[PreviewToken]) -> Callable[[Callable], Callable]:
    """Decorator to secure a WSGI function with a preview token."""

    def decorator(function: Callable) -> Callable:
        """Decorator so secure the respective function."""

        @wraps(function)
        def wrapper(*args, **kwargs) -> Any:
            """Receives a token and arguments for the original function."""
            try:
                token = token_class.get(
                    token_class.token == request.args.get('token'))
            except token_class.DoesNotExist:
                raise UNAUTHORIZED

            return function(token.obj, *args, **kwargs)

        return wrapper

    return decorator


def file_preview(presentation_class: Any) -> Callable[[Callable], Callable]:
    """Decorator to secure a WSGI function with a preview token."""

    def decorator(function: Callable) -> Callable:
        """Decorator so secure the respective function."""

        @wraps(function)
        def wrapper(obj, ident, *args, **kwargs):
            """Receives a token and arguments for the original function."""
            presentation = presentation_class(obj)

            if ident in presentation.files:
                file = File.get(
                    (File.id == ident)
                    & (File.customer == presentation.customer))
                return function(file, *args, **kwargs)

            raise UNAUTHORIZED.update(files=list(presentation.files))

        return wrapper

    return decorator
