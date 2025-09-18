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

from qt_app.ui import SectionCard, Toast


class AssistantPage(QWidget):
    def __init__(self, status_cb: Callable[[str], None], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._status_cb: Callable[[str], None] = status_cb
        self._toast = Toast(self)

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
                self._toast.show_toast(self, "Enter a question first.")
            except Exception:
                pass
            return
        # Local heuristic assistant: no external AI calls, to keep it offline.
        # Provide a helpful template answer that users can copy.
        lines: List[str] = []
        lines.append("Analysis based on your results (heuristic):")
        lines.append("")
        lines.append("- Identify IOCs marked MALICIOUS or SUSPICIOUS across multiple providers.")
        lines.append("- Prioritize items with higher scores (e.g., VT mal/susp and ThreatFox confidence > 80).")
        lines.append("- For URLs, compare multi-provider verdicts/tags; pivot to reports where available.")
        lines.append("- Cross-check OTX pulses and AbuseIPDB confidence/total_reports for corroboration.")
        lines.append("")
        lines.append("Suggested next steps:")
        lines.append("- Block high-confidence indicators; monitor medium-confidence.")
        lines.append("- Enrich with DNS/WHOIS/context before takedown.")
        lines.append("- Document evidence strings from providers in tickets.")
        self.txt_answer.setPlainText("\n".join(lines))
        try:
            self._toast.show_toast(self, "Answer generated.")
        except Exception:
            pass


