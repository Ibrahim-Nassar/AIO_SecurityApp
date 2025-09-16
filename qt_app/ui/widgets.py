# CHANGELOG: Add reusable UI widgets (BusyOverlay, Toast, SectionCard)
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
	QWidget,
	QVBoxLayout,
	QLabel,
	QFrame,
	QSizePolicy,
	QGraphicsOpacityEffect,
)


class BusyOverlay(QWidget):
	"""Semi-transparent overlay with spinner and label over a target widget.

	API:
	  show_over(target: QWidget, text: str = "Working…")
	  hide()
	"""

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		# Keep this as a child widget to avoid top-level black flicker/glitch windows
		# Use translucent background for smooth overlay on Windows
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
		self.setAutoFillBackground(False)
		self._angle = 0
		self._timer = QTimer(self)
		self._timer.timeout.connect(self._tick)
		self._bg = QColor(0, 0, 0, 90)
		self._spinner_color = QColor(255, 255, 255)
		self._label = QLabel("Working…", self)
		self._label.setStyleSheet("color: white; font-weight: 600;")
		self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.hide()
		self._text = "Working…"

	def _tick(self) -> None:
		self._angle = (self._angle + 30) % 360
		self.update()

	def show_over(self, target: QWidget, text: str = "Working…") -> None:
		try:
			self.setParent(target)
			self.setGeometry(target.rect())
			self._text = text or "Working…"
			self._label.setText(self._text)
			self._label.setGeometry(0, self.height() // 2 + 20, self.width(), 24)
		except Exception:
			pass
		super().show()
		try:
			self.raise_()
		except Exception:
			pass
		self._timer.start(90)

	def hide(self) -> None:
		try:
			self._timer.stop()
		except Exception:
			pass
		super().hide()

	def resizeEvent(self, e):  # noqa: N802
		try:
			p = self.parent()
			if isinstance(p, QWidget):
				self.setGeometry(p.rect())
				self._label.setGeometry(0, self.height() // 2 + 20, self.width(), 24)
		except Exception:
			pass
		return super().resizeEvent(e)

	def paintEvent(self, e):  # noqa: N802
		painter = QPainter(self)
		painter.fillRect(self.rect(), self._bg)
		# Simple spinner
		cx = self.width() // 2
		cy = self.height() // 2
		r = min(self.width(), self.height()) // 10
		pen = QPen(self._spinner_color)
		pen.setWidth(3)
		painter.setPen(pen)
		start = self._angle * 16
		span = 120 * 16
		painter.drawArc(cx - r, cy - r - 12, r * 2, r * 2, start, span)
		painter.end()


class Toast(QWidget):
	"""Small, fading status notification widget.

	Call show_message(parent, text) to display.
	"""

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self.setWindowFlags(
			Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setObjectName("Toast")
		lay = QVBoxLayout(self)
		lay.setContentsMargins(12, 8, 12, 8)
		self._label = QLabel("")
		self._label.setStyleSheet("color: #FFFFFF; font-weight: 600;")
		lay.addWidget(self._label)
		# Dark slate background and subtle border for light theme
		self._bg = QColor(31, 41, 55)
		self._border = QColor(17, 24, 39)
		self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
		self._opacity = QGraphicsOpacityEffect(self)
		self._opacity.setOpacity(0.0)
		self.setGraphicsEffect(self._opacity)
		self._anim = QPropertyAnimation(self._opacity, b"opacity", self)
		self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

	def paintEvent(self, e):  # noqa: N802
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setBrush(self._bg)
		painter.setPen(QPen(self._border, 1))
		rect = self.rect()
		rect.adjust(0, 0, -1, -1)
		radius = 6
		painter.drawRoundedRect(rect, radius, radius)
		painter.end()

	def show_message(self, parent: QWidget, text: str, timeout_ms: int = 2500) -> None:
		self._label.setText(text)
		# Size to content
		self.adjustSize()
		# Position bottom-right with margin (20 px)
		gp = parent.mapToGlobal(QPoint(0, 0))
		x = gp.x() + parent.width() - self.width() - 20
		y = gp.y() + parent.height() - self.height() - 20
		self.move(x, y)
		super().show()
		self.raise_()
		try:
			self._anim.stop()
		except Exception:
			pass
		self._anim.setDuration(150)
		self._anim.setStartValue(0.0)
		self._anim.setEndValue(1.0)
		self._anim.start()
		QTimer.singleShot(timeout_ms, self._fade_out)

	# New API alias matching spec
	def show_toast(self, parent: QWidget, text: str, kind: str = "info", msec: int = 1800) -> None:
		# Map kind to subtle color tint if needed in future
		try:
			self.show_message(parent, text, msec)
		except Exception:
			pass

	def _fade_out(self) -> None:
		try:
			self._anim.stop()
		except Exception:
			pass
		self._anim.setDuration(250)
		self._anim.setStartValue(1.0)
		self._anim.setEndValue(0.0)
		self._anim.start()
		def _cleanup() -> None:
			try:
				self.hide()
				self.deleteLater()
			except Exception:
				pass
		QTimer.singleShot(self._anim.duration(), _cleanup)


class SectionCard(QFrame):
	"""Rounded panel usable as a titled card container."""

	def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self.setObjectName("SectionCard")
		lay = QVBoxLayout(self)
		lay.setContentsMargins(12, 12, 12, 12)
		lay.setSpacing(8)
		if title:
			head = QLabel(title)
			head.setObjectName("title")
			head.setAlignment(Qt.AlignmentFlag.AlignHCenter)
			lay.addWidget(head)
		self._body_layout = lay

	@property
	def body(self) -> QVBoxLayout:
		return self._body_layout 