# CHANGELOG:
# - Introduced design system constants (spacing, radius, palette) and app-wide QSS
# - Exposes apply_app_styles(app) to theme the application consistently

# CHANGELOG: Add Qt design system theme (colors, typography, spacing) and QSS loader
from __future__ import annotations

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

# Typography and spacing tokens
FONT_SIZE_BASE = 12
FONT_SIZE_SMALL = 11
SPACING = 8
RADIUS = 10

# Palette tokens (accessible light theme)
PRIMARY = QColor(0, 128, 128)           # teal 600-ish
PRIMARY_HOVER = QColor(0, 110, 110)     # teal 700-ish
BG = QColor(246, 249, 252)              # very light gray/blue
CARD_BG = QColor(255, 255, 255)
BORDER = QColor(210, 220, 230)          # neutral 300
TEXT_PRIMARY = QColor(20, 24, 28)       # near-black
TEXT_MUTED = QColor(100, 112, 120)      # neutral 600
SUCCESS = QColor(16, 138, 72)
WARNING = QColor(194, 120, 3)
ERROR = QColor(178, 34, 34)


def _apply_palette(app: QApplication) -> None:
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, BG)
    pal.setColor(QPalette.ColorRole.Base, CARD_BG)
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(243, 247, 250))
    pal.setColor(QPalette.ColorRole.Button, CARD_BG)
    pal.setColor(QPalette.ColorRole.Text, TEXT_PRIMARY)
    pal.setColor(QPalette.ColorRole.WindowText, TEXT_PRIMARY)
    pal.setColor(QPalette.ColorRole.ButtonText, TEXT_PRIMARY)
    pal.setColor(QPalette.ColorRole.Highlight, PRIMARY)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(pal)


def _qss() -> str:
    # Base app styles
    return f"""
    QWidget {{
        font-family: -apple-system, 'Segoe UI', Roboto, Arial, sans-serif;
        font-size: {FONT_SIZE_BASE}pt;
        color: {TEXT_PRIMARY.name()};
        background: {BG.name()};
    }}
    QLabel[muted='true'] {{
        color: {TEXT_MUTED.name()};
        font-size: {FONT_SIZE_SMALL}pt;
    }}
    QFrame#SectionCard {{
        background: {CARD_BG.name()};
        border: 1px solid {BORDER.name()};
        border-radius: {RADIUS}px;
    }}
    QFrame#SectionCard > QLabel.title {{
        font-weight: 600;
        color: {TEXT_PRIMARY.name()};
    }}
    QToolBar {{
        background: {CARD_BG.name()};
        border: 0px;
        padding: 4px;
    }}
    QToolButton, QPushButton {{
        padding: 6px 12px;
        border-radius: {RADIUS - 4}px;
        min-height: 28px;
        background: {CARD_BG.name()};
        border: 1px solid {BORDER.name()};
    }}
    QPushButton:hover {{
        background: #E7F4F4;
        border-color: {PRIMARY.name()};
    }}
    QPushButton:pressed {{
        background: #D6ECEC;
        border-color: {PRIMARY_HOVER.name()};
    }}
    QPushButton:focus {{
        outline: none;
        border: 1px solid {PRIMARY.name()};
    }}
    /* Dynamic property class selector for primary buttons */
    QPushButton[class="PrimaryButton"], QPushButton.primary {{
        background: {PRIMARY.name()};
        color: white;
        font-weight: 600;
        border: 1px solid {PRIMARY.name()};
    }}
    QPushButton[class="PrimaryButton"]:hover, QPushButton.primary:hover {{
        background: {PRIMARY_HOVER.name()};
        border-color: {PRIMARY_HOVER.name()};
    }}
    /* Secondary role */
    QPushButton[class="SecondaryButton"] {{
        background: {CARD_BG.name()};
        color: {TEXT_PRIMARY.name()};
        border: 1px solid {BORDER.name()};
    }}
    QPushButton[class="SecondaryButton"]:hover {{
        background: #F3F8FA;
        border-color: {PRIMARY.name()};
    }}
    /* Destructive role */
    QPushButton[class="DestructiveButton"] {{
        background: {ERROR.name()};
        color: white;
        border: 1px solid {ERROR.name()};
    }}
    QPushButton[class="DestructiveButton"]:hover {{
        background: {ERROR.darker(110).name()};
        border-color: {ERROR.darker(120).name()};
    }}
    QPushButton:disabled {{
        opacity: 0.6;
    }}
    QGroupBox {{
        border: 1px solid {BORDER.name()};
        border-radius: {RADIUS}px;
        margin-top: 8px;
        padding-top: 12px;
        background: {CARD_BG.name()};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        top: -4px;
        padding: 0px 4px;
        background: transparent;
        color: {TEXT_PRIMARY.name()};
        font-weight: 600;
    }}
    QLineEdit, QPlainTextEdit {{
        min-height: 28px;
        border: 1px solid {BORDER.name()};
        border-radius: {RADIUS - 4}px;
        background: {CARD_BG.name()};
        padding: 4px 6px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {PRIMARY.name()};
        outline: none;
    }}
    QTableView {{
        background: {CARD_BG.name()};
        border: 1px solid {BORDER.name()};
        gridline-color: {BORDER.name()};
        selection-background-color: {PRIMARY.name()};
        selection-color: white;
        alternate-background-color: rgba(0,0,0,0.02);
    }}
    QHeaderView::section {{
        background: {PRIMARY.name()};
        color: white;
        padding: 6px;
        border: 0px;
    }}
    QSplitter::handle {{
        background: {BORDER.name()};
        width: 4px;
        margin: 0;
    }}
    QProgressBar {{
        border: 1px solid {BORDER.name()};
        border-radius: {RADIUS - 4}px;
        background: {CARD_BG.name()};
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {PRIMARY.name()};
    }}
    """


def apply_app_styles(app: QApplication) -> None:
    _apply_palette(app)
    app.setStyleSheet(_qss()) 