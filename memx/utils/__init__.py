from typing_extensions import TypeAliasType

# NOTE: probably we shouldn't include list[JSON]
# In summary; anything that can be serialized with orjson.dumps()
JSON = TypeAliasType("JSON", "dict[str, JSON] | list[JSON] | str | int | float | bool | None")
