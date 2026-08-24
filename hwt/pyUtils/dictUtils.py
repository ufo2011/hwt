from _typing import TypeVar

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


def dictMerge(*dicts: tuple[dict[KeyT, ValueT], ...], recursively=False) -> dict[KeyT, ValueT]:
    """
    :note: input diects are unmodified and the returned dict is a new instance
        but key and value objects are the original
        (recursively may create new instance of value in order to avoid modification of original)
    """
    d: dict[KeyT, ValueT] = {}
    isFirstDict = True
    for dIn in dicts:
        if recursively and not isFirstDict:
            for k, v in dIn.items():
                if isinstance(v, dict):
                    existing = d.get(k, None)
                    if existing is not None and isinstance(existing, dict):
                        d[k] = dictMerge(existing, v)
                        continue
                d[k] = v
            
        else:
            d.update(dIn)

        isFirstDict = False

    return d
    
