import importlib
import pkgutil
from src.pipelines.base import Pipeline


_REGISTRY: dict[str, type[Pipeline]] = {}


def discover_pipelines() -> dict[str, type[Pipeline]]:
    """Walk src/pipelines/ for subpackages exposing a Pipeline subclass."""
    global _REGISTRY
    if _REGISTRY:
        return _REGISTRY

    import src.pipelines as pkg
    for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
        if not ispkg:
            continue
        try:
            mod = importlib.import_module(f"src.pipelines.{modname}.pipeline")
        except ModuleNotFoundError:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, Pipeline)
                and cls is not Pipeline
            ):
                _REGISTRY[cls.name] = cls
    return _REGISTRY


def get_pipeline(name: str) -> type[Pipeline]:
    discover_pipelines()
    if name not in _REGISTRY:
        raise KeyError(f"Pipeline '{name}' not found. Known: {list(_REGISTRY)}")
    return _REGISTRY[name]
