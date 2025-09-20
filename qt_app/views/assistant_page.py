from __future__ import annotations

from typing import Callable, Optional, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
)

from qt_app.ui import SectionCard, ToastManager


class AssistantPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        head = QLabel("AI Assistant")
        head.setProperty("muted", True)
        root.addWidget(head)

        card = SectionCard("Explain or summarize IOC results")
        lay = card.body

        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setPlaceholderText("Ask a question about your IOC results, e.g.\nSummarize which IOCs are most risky and why.")
        self.txt_prompt.setMinimumHeight(100)
        lay.addWidget(self.txt_prompt)

        btns = QHBoxLayout()
        self.btn_answer = QPushButton("Answer")
        btns.addWidget(self.btn_answer)
        btns.addStretch(1)
        lay.addLayout(btns)

        self.txt_answer = QPlainTextEdit()
        self.txt_answer.setReadOnly(True)
        self.txt_answer.setMinimumHeight(220)
        lay.addWidget(self.txt_answer)

        root.addWidget(card)

        self.btn_answer.clicked.connect(self._on_answer)

    def _update_status(self, msg: str) -> None:
        self._status_cb(msg)

    def _on_answer(self) -> None:
        prompt = (self.txt_prompt.toPlainText() or "").strip()
        if not prompt:
            try:
                ToastManager.instance(self).show("Enter a question first.", "warn")
            except Exception:
                pass
            return
        
        # Placeholder for AI assistant functionality
        self.txt_answer.setPlainText("AI assistant feature is not yet implemented.")
        try:
            ToastManager.instance(self).show("AI assistant feature coming soon.", "info")
        except Exception:
            pass


