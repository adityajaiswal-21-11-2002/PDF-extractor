"""
Bootstrap: provide pkg_resources for crewai (uses setuptools; Render venv may lack it).
Injects into sys.modules before crewai is imported.
"""
import sys

if "pkg_resources" not in sys.modules:
    try:
        import pkg_resources
    except ImportError:
        import importlib.metadata as metadata

        class _Distribution:
            def __init__(self, name: str):
                self._dist = metadata.distribution(name)

            @property
            def version(self):
                return self._dist.version

        class _Shim:
            @staticmethod
            def get_distribution(name: str):
                return _Distribution(name)

        sys.modules["pkg_resources"] = _Shim()
