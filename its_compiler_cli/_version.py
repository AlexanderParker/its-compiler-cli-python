"""
Single source of truth for the CLI version.

Resolved from the installed distribution metadata rather than written here, so
it cannot drift from pyproject.toml. A hardcoded copy in main.py shadowed the
package value and made 1.1.0 report itself as 0.1.0.

This lives in its own module because __init__.py imports from main.py, so
main.py importing the version back from __init__.py would be circular.
"""

from importlib.metadata import PackageNotFoundError, version as _package_version

try:
    __version__ = _package_version("its-compiler-cli")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
