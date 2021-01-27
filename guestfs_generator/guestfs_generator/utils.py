"""
utility functions
"""
from functools import update_wrapper

# pylint: disable=c-extension-no-member
import orjson

orjson_loads = orjson.loads


def orjson_dumps(value, *, default) -> str:
    """
    orjson.dumps returns bytes
    this needs to be decoded into a str in order to match built-in
    json.dumps

    from:
    https://pydantic-docs.helpmanual.io/usage/exporting_models/#custom-json-deserialisation
    """
    return orjson.dumps(value, default=default).decode()


update_wrapper(wrapper=orjson_dumps, wrapped=orjson.dumps)
