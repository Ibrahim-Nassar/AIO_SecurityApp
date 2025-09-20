# CHANGELOG: Add reusable UI widgets (BusyOverlay, Toast, SectionCard) + ToastManager singleton
from __future__ import annotations

import time
from typing import Optional, Literal

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QObject, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QKeySequence
from PySide6.QtWidgets import (
	QWidget,
	QVBoxLayout,
	QLabel,
	QFrame,
	QSizePolicy,
	QGraphicsOpacityEffect,
	QApplication,
)

# Import design tokens
from .theme import (
	COLOR_BG_CARD, COLOR_BORDER, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
	COLOR_SHADOW, RADIUS_MD, SPACE_2, SPACE_3, SPACE_4,
	COLOR_TOAST_INFO_BG, COLOR_TOAST_INFO_BORDER, COLOR_TOAST_SUCCESS_BORDER,
	COLOR_TOAST_WARNING_BORDER, COLOR_TOAST_ERROR_BORDER,
	COLOR_OVERLAY_BG, COLOR_OVERLAY_TEXT
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
		# Cleaner backdrop using design tokens
		self._bg = COLOR_OVERLAY_BG
		self._spinner_color = COLOR_OVERLAY_TEXT
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
			self._label.setGeometry(0, self.height() // 2 + SPACE_4 + SPACE_1, self.width(), SPACE_4 + SPACE_2)
			# Track parent geometry changes via eventFilter
			try:
				if isinstance(target, QWidget):
					target.removeEventFilter(self)
					target.installEventFilter(self)
			except Exception:
				pass
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
		# Avoid stale filter
		try:
			p = self.parent()
			if isinstance(p, QWidget):
				p.removeEventFilter(self)
		except Exception:
			pass
		super().hide()

	def eventFilter(self, watched: QObject, event: QEvent) -> bool:
		try:
			if watched is self.parent() and isinstance(watched, QWidget):
				if event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show, QEvent.Type.Hide):
					self.setGeometry(watched.rect())
					self._label.setGeometry(0, self.height() // 2 + SPACE_4 + SPACE_1, self.width(), SPACE_4 + SPACE_2)
		except Exception:
			pass
		return False

	def resizeEvent(self, e):  # noqa: N802
		try:
			p = self.parent()
			if isinstance(p, QWidget):
				self.setGeometry(p.rect())
				self._label.setGeometry(0, self.height() // 2 + SPACE_4 + SPACE_1, self.width(), SPACE_4 + SPACE_2)
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
		painter.drawArc(cx - r, cy - r - SPACE_3, r * 2, r * 2, start, span)
		painter.end()


class Toast(QWidget):
	"""Small, fading status notification widget.
	
	NOTE: Do not instantiate directly. Use ToastManager.instance(parent).show() instead.
	"""

	def __init__(self, parent: Optional[QWidget] = None) -> None:
		super().__init__(parent)
		self.setWindowFlags(
			Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
		)
		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		# REMOVED: WA_NoSystemBackground and WA_TranslucentBackground to allow solid backgrounds
		self.setObjectName("Toast")
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Allow focus for Esc key
		lay = QVBoxLayout(self)
		lay.setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
		self._label = QLabel("")
		self._label.setStyleSheet("color: #FFFFFF; font-weight: 600; background: transparent;")
		lay.addWidget(self._label)
		# Background and border default (info) - using design tokens
		self._bg = COLOR_BG_CARD
		self._border = COLOR_BORDER
		self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
		# Set a solid background color to ensure proper rendering
		self.setAutoFillBackground(True)
		# No opacity effects - toast will appear instantly and fade by simple hide/show

	def keyPressEvent(self, event):  # noqa: N802
		"""Handle Esc key to dismiss toast."""
		if event.key() == Qt.Key.Key_Escape:
			self._fade_out()
		else:
			super().keyPressEvent(event)

	def paintEvent(self, e):  # noqa: N802
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		
		rect = self.rect()
		radius = RADIUS_MD  # Use design token
		
		# Fill entire background first to ensure no white showing through
		painter.fillRect(rect, self._bg)
		
		# Solid opaque background - no transparency
		solid_bg = QColor(self._bg)
		solid_bg.setAlpha(255)  # Force fully opaque
		painter.setBrush(solid_bg)
		painter.setPen(QPen(self._border, 2))  # Thicker border for better visibility
		painter.drawRoundedRect(rect, radius, radius)
		painter.end()

	def _set_kind(self, kind: str) -> None:
		"""Set toast colors based on kind using design tokens."""
		kind = (kind or "info").lower()
		if kind == "success":
			self._bg = COLOR_SUCCESS
			self._border = COLOR_TOAST_SUCCESS_BORDER
		elif kind == "warn" or kind == "warning":
			self._bg = COLOR_WARNING
			self._border = COLOR_TOAST_WARNING_BORDER
		elif kind == "error":
			self._bg = COLOR_ERROR
			self._border = COLOR_TOAST_ERROR_BORDER
		else:  # info
			self._bg = COLOR_TOAST_INFO_BG
			self._border = COLOR_TOAST_INFO_BORDER
		# Force repaint with new colors
		self.update()

	def _show(self, parent: QWidget, text: str, kind: str = "info", msec: int = 2000) -> None:
		"""Internal method to show the toast."""
		self._set_kind(kind)
		self._label.setText(text)
		# Size to content
		self.adjustSize()
		# Position center of the main window (not just the immediate parent)
		main_window = self._find_main_window(parent)
		if main_window:
			gp = main_window.mapToGlobal(QPoint(0, 0))
			x = gp.x() + int((main_window.width() - self.width()) / 2)
			y = gp.y() + int((main_window.height() - self.height()) / 2)
		else:
			# Fallback to parent centering
			gp = parent.mapToGlobal(QPoint(0, 0))
			x = gp.x() + int((parent.width() - self.width()) / 2)
			y = gp.y() + int((parent.height() - self.height()) / 2)
		self.move(x, y)
		super().show()
		self.raise_()
		self.setFocus()  # Allow Esc key to work
		# Show immediately with full opacity - no fade animation
		QTimer.singleShot(msec, self._fade_out)

	def _find_main_window(self, widget: QWidget) -> Optional[QWidget]:
		"""Find the top-level main window."""
		current = widget
		while current is not None:
			if current.isWindow() and hasattr(current, 'setStatusBar'):
				return current
			current = current.parent()
		return None

	def _fade_out(self) -> None:
		# Hide immediately - no fade animation
		try:
			self.hide()
		except Exception:
			pass


class ToastManager(QObject):
	"""Singleton manager for displaying centered toasts.
	
	Usage:
	  ToastManager.instance(parent_widget).show("Message", "success", 3000)
	"""
	
	_instances: dict[QWidget, 'ToastManager'] = {}
	
	def __init__(self, main_window: QWidget) -> None:
		super().__init__(main_window)
		self._main_window = main_window
		self._toast: Optional[Toast] = None
		self._last_text = ""
		self._last_kind = ""
		self._last_timestamp = 0.0
		
		# Install event filter on main window for re-positioning
		main_window.installEventFilter(self)
	
	@classmethod
	def instance(cls, parent: QWidget) -> 'ToastManager':
		"""Get or create ToastManager instance for the main window."""
		# Find the main window
		main_window = cls._find_main_window(parent)
		if main_window is None:
			main_window = parent
		
		if main_window not in cls._instances:
			cls._instances[main_window] = cls(main_window)
		return cls._instances[main_window]
	
	@staticmethod
	def _find_main_window(widget: QWidget) -> Optional[QWidget]:
		"""Find the top-level main window."""
		current = widget
		while current is not None:
			if current.isWindow() and hasattr(current, 'setStatusBar'):
				return current
			current = current.parent()
		return None
	
	def show(self, text: str, kind: Literal["info", "success", "warn", "error"] = "info", msec: int = 2000) -> None:
		"""Show a toast message. Coalesces identical messages within 2 seconds."""
		text = (text or "").strip()
		if not text:
			return
		
		# Coalesce identical messages within 2 seconds
		current_time = time.time()
		if (text.lower() == self._last_text.lower() and 
		    kind == self._last_kind and 
		    current_time - self._last_timestamp < 2.0):
			return
		
		self._last_text = text
		self._last_kind = kind
		self._last_timestamp = current_time
		
		# Hide existing toast if showing
		if self._toast and self._toast.isVisible():
			self._toast.hide()
		
		# Create or reuse toast
		if not self._toast:
			self._toast = Toast(self._main_window)
		
		# Show the toast
		self._toast._show(self._main_window, text, kind, msec)
	
	def eventFilter(self, watched: QObject, event: QEvent) -> bool:
		"""Re-center toast when main window moves or resizes."""
		if watched is self._main_window and self._toast and self._toast.isVisible():
			if event.type() in (QEvent.Type.Resize, QEvent.Type.Move, QEvent.Type.Show):
				# Re-center the toast
				try:
					gp = self._main_window.mapToGlobal(QPoint(0, 0))
					x = gp.x() + int((self._main_window.width() - self._toast.width()) / 2)
					y = gp.y() + int((self._main_window.height() - self._toast.height()) / 2)
					self._toast.move(x, y)
				except Exception:
					pass
		return False


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