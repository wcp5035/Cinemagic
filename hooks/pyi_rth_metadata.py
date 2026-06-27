import sys

if getattr(sys, "frozen", False):
    import importlib.metadata as _metadata

    _original_version = _metadata.version

    def _version(name: str) -> str:
        candidates = {name, name.replace("_", "-"), name.replace("-", "_")}
        for candidate in candidates:
            try:
                return _original_version(candidate)
            except _metadata.PackageNotFoundError:
                continue
        return "0.0.0"

    _metadata.version = _version  # type: ignore[method-assign]
