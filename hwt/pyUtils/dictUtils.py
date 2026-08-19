from _typing import TypeVar

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


def dictMerge(*dicts: tuple[dict[KeyT, ValueT], ...]) -> dict[KeyT, ValueT]:
    d: dict[KeyT, ValueT] = {}
    for dIn in dicts:
        d.update(dIn)
    return d
    
