"""ioc_checker compatibility package.

This package remains as a thin compatibility layer to preserve legacy imports.
All functionality has moved to `ioc_core` and `qt_app`.
- CLI: `ioc_checker.cli.urls` delegates to `ioc_core`.
- Models/Cache/Helpers: re-exported from `ioc_core`.
- Providers: re-exported classes from `ioc_core.services`.

New code should depend directly on `ioc_core`.
"""


