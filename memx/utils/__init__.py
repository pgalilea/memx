import inspect
from collections.abc import Callable


def filter_kwargs(fn: Callable, _kwargs: dict) -> dict:
    """Filter the kwargs of a function to only include the ones that are in the signature"""

    signature = inspect.signature(fn)
    parameters = signature.parameters

    return {k: v for k, v in _kwargs.items() if k in parameters.keys()}
