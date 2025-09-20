# CHANGELOG: Initial UI helpers package exposing theme and widgets

from .theme import apply_app_styles, SPACING, RADIUS
from . import widgets as _widgets

# Re-export commonly used widgets for convenience
BusyOverlay = _widgets.BusyOverlay
ToastManager = _widgets.ToastManager
SectionCard = _widgets.SectionCard

# Legacy Toast export - deprecated, use ToastManager instead
Toast = _widgets.Toast

__all__ = [
    "apply_app_styles",
    "SPACING",
    "RADIUS",
    "BusyOverlay",
    "ToastManager",
    "SectionCard",
    "Toast",  # deprecated
] 