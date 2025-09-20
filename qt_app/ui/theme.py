# CHANGELOG:
# - Introduced design system constants (spacing, radius, palette) and app-wide QSS
# - Exposes apply_app_styles(app) to theme the application consistently
# - Added comprehensive design tokens and removed hardcoded hex values

# CHANGELOG: Add Qt design system theme (colors, typography, spacing) and QSS loader
from __future__ import annotations

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

# === DESIGN TOKENS ===

# Colors (QColor)
COLOR_BG = QColor(246, 249, 252)              # Background
COLOR_BG_CARD = QColor(255, 255, 255)         # Card/widget background
COLOR_TEXT = QColor(20, 24, 28)               # Primary text
COLOR_TEXT_MUTED = QColor(100, 112, 120)      # Muted text
COLOR_PRIMARY = QColor(0, 128, 128)           # Primary brand color
COLOR_PRIMARY_HOVER = QColor(0, 110, 110)     # Primary hover state
COLOR_SUCCESS = QColor(16, 138, 72)           # Success state (#108A48)
COLOR_WARNING = QColor(194, 120, 3)           # Warning state (#C27803)
COLOR_ERROR = QColor(178, 34, 34)             # Error state (#B22222)
COLOR_BORDER = QColor(210, 220, 230)          # Border color
COLOR_SHADOW = QColor(0, 0, 0, 40)            # Shadow color with alpha

# Toast-specific colors for proper contrast
COLOR_TOAST_INFO_BG = QColor(31, 41, 55)      # #1F2937
COLOR_TOAST_INFO_BORDER = QColor(17, 24, 39)  # #111827
COLOR_TOAST_SUCCESS_BORDER = QColor(10, 95, 50)   # #0A5F32
COLOR_TOAST_WARNING_BORDER = QColor(145, 90, 3)   # #915A03
COLOR_TOAST_ERROR_BORDER = QColor(120, 20, 20)    # #781414

# Overlay colors
COLOR_OVERLAY_BG = QColor(0, 0, 0, 110)       # Semi-transparent black
COLOR_OVERLAY_TEXT = QColor(255, 255, 255)    # White text on overlay

# Additional semantic colors
COLOR_PRIMARY_LIGHT = QColor(231, 244, 244)   # #E7F4F4
COLOR_PRIMARY_LIGHTER = QColor(214, 236, 236) # #D6ECEC
COLOR_HOVER_SECONDARY = QColor(243, 248, 250) # #F3F8FA
COLOR_ALTERNATE_ROW = QColor(0, 0, 0, 5)      # rgba(0,0,0,0.02)

# Radii
RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 12

# Spacing
SPACE_0 = 0
SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16

# Font sizes
FONT_SM = 11
FONT_MD = 13
FONT_LG = 15

# Legacy compatibility
FONT_SIZE_BASE = FONT_MD
FONT_SIZE_SMALL = FONT_SM
SPACING = SPACE_2
RADIUS = RADIUS_LG

# Elevation/Shadow
ELEV_0 = "none"
ELEV_1 = f"2px 3px 2px {COLOR_SHADOW.name()}"  # Subtle shadow

# Typography and spacing tokens (legacy compatibility)
PRIMARY = COLOR_PRIMARY
PRIMARY_HOVER = COLOR_PRIMARY_HOVER
BG = COLOR_BG
CARD_BG = COLOR_BG_CARD
BORDER = COLOR_BORDER
TEXT_PRIMARY = COLOR_TEXT
TEXT_MUTED = COLOR_TEXT_MUTED
SUCCESS = COLOR_SUCCESS
WARNING = COLOR_WARNING
ERROR = COLOR_ERROR


def color_hex(c: QColor) -> str:
    """Convert QColor to hex string."""
    return c.name()


def _apply_palette(app: QApplication) -> None:
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, COLOR_BG)
    pal.setColor(QPalette.ColorRole.Base, COLOR_BG_CARD)
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(243, 247, 250))
    pal.setColor(QPalette.ColorRole.Button, COLOR_BG_CARD)
    pal.setColor(QPalette.ColorRole.Text, COLOR_TEXT)
    pal.setColor(QPalette.ColorRole.WindowText, COLOR_TEXT)
    pal.setColor(QPalette.ColorRole.ButtonText, COLOR_TEXT)
    pal.setColor(QPalette.ColorRole.Highlight, COLOR_PRIMARY)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(pal)


def _qss() -> str:
    # Base app styles using only design tokens
    return f"""
    QWidget {{
        font-family: -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
        font-size: {FONT_MD}pt;
        color: {color_hex(COLOR_TEXT)};
        background: {color_hex(COLOR_BG)};
    }}
    QLabel[muted='true'] {{
        color: {color_hex(COLOR_TEXT_MUTED)};
        font-size: {FONT_SM}pt;
    }}
    QFrame#SectionCard {{
        background: {color_hex(COLOR_BG_CARD)};
        border: 1px solid {color_hex(COLOR_BORDER)};
        border-radius: {RADIUS_LG}px;
    }}
    QFrame#SectionCard > QLabel.title {{
        font-weight: 600;
        color: {color_hex(COLOR_TEXT)};
    }}
    QToolBar {{
        background: {color_hex(COLOR_BG_CARD)};
        border: 0px;
        padding: {SPACE_1}px;
    }}
    QToolButton, QPushButton {{
        padding: {SPACE_1}px {SPACE_3}px;
        border-radius: {RADIUS_SM}px;
        min-height: 28px;
        background: {color_hex(COLOR_BG_CARD)};
        border: 1px solid {color_hex(COLOR_BORDER)};
    }}
    QPushButton:hover {{
        background: {color_hex(COLOR_PRIMARY_LIGHT)};
        border-color: {color_hex(COLOR_PRIMARY)};
    }}
    QPushButton:pressed {{
        background: {color_hex(COLOR_PRIMARY_LIGHTER)};
        border-color: {color_hex(COLOR_PRIMARY_HOVER)};
    }}
    QPushButton:focus {{
        outline: none;
        border: 1px solid {color_hex(COLOR_PRIMARY)};
    }}
    /* Dynamic property class selector for primary buttons */
    QPushButton[class="PrimaryButton"], QPushButton.primary {{
        background: {color_hex(COLOR_PRIMARY)};
        color: white;
        font-weight: 600;
        border: 1px solid {color_hex(COLOR_PRIMARY)};
    }}
    QPushButton[class="PrimaryButton"]:hover, QPushButton.primary:hover {{
        background: {color_hex(COLOR_PRIMARY_HOVER)};
        border-color: {color_hex(COLOR_PRIMARY_HOVER)};
    }}
    /* Secondary role */
    QPushButton[class="SecondaryButton"] {{
        background: {color_hex(COLOR_BG_CARD)};
        color: {color_hex(COLOR_TEXT)};
        border: 1px solid {color_hex(COLOR_BORDER)};
    }}
    QPushButton[class="SecondaryButton"]:hover {{
        background: {color_hex(COLOR_HOVER_SECONDARY)};
        border-color: {color_hex(COLOR_PRIMARY)};
    }}
    /* Destructive role */
    QPushButton[class="DestructiveButton"] {{
        background: {color_hex(COLOR_ERROR)};
        color: white;
        border: 1px solid {color_hex(COLOR_ERROR)};
    }}
    QPushButton[class="DestructiveButton"]:hover {{
        background: {color_hex(COLOR_ERROR.darker(110))};
        border-color: {color_hex(COLOR_ERROR.darker(120))};
    }}
    QPushButton:disabled {{
        opacity: 0.6;
    }}
    QGroupBox {{
        border: 1px solid {color_hex(COLOR_BORDER)};
        border-radius: {RADIUS_LG}px;
        margin-top: {SPACE_2}px;
        padding-top: {SPACE_3}px;
        background: {color_hex(COLOR_BG_CARD)};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {SPACE_3}px;
        top: -{SPACE_1}px;
        padding: 0px {SPACE_1}px;
        background: transparent;
        color: {color_hex(COLOR_TEXT)};
        font-weight: 600;
    }}
    QLineEdit, QPlainTextEdit {{
        min-height: 28px;
        border: 1px solid {color_hex(COLOR_BORDER)};
        border-radius: {RADIUS_SM}px;
        background: {color_hex(COLOR_BG_CARD)};
        padding: {SPACE_1}px {SPACE_1}px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {color_hex(COLOR_PRIMARY)};
        outline: none;
    }}
    QTableView {{
        background: {color_hex(COLOR_BG_CARD)};
        border: 1px solid {color_hex(COLOR_BORDER)};
        gridline-color: {color_hex(COLOR_BORDER)};
        selection-background-color: {color_hex(COLOR_PRIMARY)};
        selection-color: white;
        alternate-background-color: rgba(0,0,0,0.02);
    }}
    QHeaderView::section {{
        background: {color_hex(COLOR_PRIMARY)};
        color: white;
        padding: {SPACE_1}px;
        border: 0px;
    }}
    QSplitter::handle {{
        background: {color_hex(COLOR_BORDER)};
        width: {SPACE_1}px;
        margin: 0;
    }}
    QProgressBar {{
        border: 1px solid {color_hex(COLOR_BORDER)};
        border-radius: {RADIUS_SM}px;
        background: {color_hex(COLOR_BG_CARD)};
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {color_hex(COLOR_PRIMARY)};
    }}
    """


def apply_app_styles(app: QApplication) -> None:
    _apply_palette(app)
    app.setStyleSheet(_qss()) 