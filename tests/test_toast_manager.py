"""Tests for ToastManager singleton functionality."""

import time
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QLabel

from qt_app.ui.widgets import ToastManager


class DummyMainWindow(QMainWindow):
    """Dummy main window for testing."""
    
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Test Window"))
        self.setCentralWidget(central)


class TestToastManager:
    """Test ToastManager functionality."""
    
    def test_singleton_behavior(self, qtbot):
        """Test that ToastManager behaves as a singleton per main window."""
        window1 = DummyMainWindow()
        window2 = DummyMainWindow()
        qtbot.addWidget(window1)
        qtbot.addWidget(window2)
        
        # Same window should return same instance
        manager1a = ToastManager.instance(window1)
        manager1b = ToastManager.instance(window1)
        assert manager1a is manager1b
        
        # Different windows should return different instances
        manager2 = ToastManager.instance(window2)
        assert manager1a is not manager2
    
    def test_toast_display_and_centering(self, qtbot):
        """Test that toast is displayed and centered over main window."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        manager.show("Test message", "info")
        
        # Toast should be created and visible
        assert manager._toast is not None
        assert manager._toast.isVisible()
        
        # Toast should be centered within ±8px tolerance
        window_center = window.geometry().center()
        toast_center = QPoint(
            manager._toast.x() + manager._toast.width() // 2,
            manager._toast.y() + manager._toast.height() // 2
        )
        
        # Check centering with tolerance
        assert abs(window_center.x() - toast_center.x()) <= 8
        assert abs(window_center.y() - toast_center.y()) <= 8
    
    def test_message_coalescing(self, qtbot):
        """Test that identical messages within 2 seconds are coalesced."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        # Show same message twice within 1 second
        manager.show("Hello", "info")
        first_toast = manager._toast
        
        time.sleep(0.5)  # Wait 0.5 seconds
        manager.show("Hello", "info")  # Same message
        
        # Should still be the same toast instance
        assert manager._toast is first_toast
        assert manager._toast.isVisible()
    
    @patch('time.time')
    def test_message_coalescing_timeout(self, mock_time, qtbot):
        """Test that messages are not coalesced after 2 seconds."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        # Mock time progression
        mock_time.return_value = 1000.0
        manager.show("Hello", "info")
        first_timestamp = manager._last_timestamp
        
        # Advance time by 3 seconds
        mock_time.return_value = 1003.0
        manager.show("Hello", "info")  # Same message but after timeout
        
        # Should update timestamp (message is not coalesced)
        assert manager._last_timestamp > first_timestamp
    
    def test_different_messages_not_coalesced(self, qtbot):
        """Test that different messages are not coalesced."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        manager.show("Message 1", "info")
        first_text = manager._last_text
        
        manager.show("Message 2", "info")  # Different message
        
        # Should update to new message
        assert manager._last_text != first_text
        assert manager._last_text == "Message 2"
    
    def test_different_kinds_not_coalesced(self, qtbot):
        """Test that same text with different kinds are not coalesced."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        manager.show("Hello", "info")
        manager.show("Hello", "error")  # Same text, different kind
        
        # Should update kind
        assert manager._last_kind == "error"
    
    def test_toast_colors(self, qtbot):
        """Test that toast colors are set correctly for different kinds."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        # Test each kind
        test_cases = [
            ("info", (31, 41, 55), (17, 24, 39)),
            ("success", (16, 138, 72), (10, 95, 50)),
            ("warn", (194, 120, 3), (145, 90, 3)),
            ("error", (178, 34, 34), (120, 20, 20)),
        ]
        
        for kind, expected_bg, expected_border in test_cases:
            manager.show(f"Test {kind}", kind)
            
            # Check colors
            toast = manager._toast
            assert toast._bg.red() == expected_bg[0]
            assert toast._bg.green() == expected_bg[1]
            assert toast._bg.blue() == expected_bg[2]
            
            assert toast._border.red() == expected_border[0]
            assert toast._border.green() == expected_border[1]
            assert toast._border.blue() == expected_border[2]
    
    def test_empty_message_ignored(self, qtbot):
        """Test that empty messages are ignored."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        
        # Try to show empty messages
        manager.show("", "info")
        manager.show("   ", "info")
        manager.show(None, "info")
        
        # No toast should be created
        assert manager._toast is None or not manager._toast.isVisible()
    
    def test_window_event_recentering(self, qtbot):
        """Test that toast is re-centered when window moves/resizes."""
        window = DummyMainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)
        
        manager = ToastManager.instance(window)
        manager.show("Test", "info")
        
        original_pos = manager._toast.pos()
        
        # Move window
        window.move(200, 200)
        qtbot.wait(10)  # Allow event processing
        
        # Toast should have moved too
        new_pos = manager._toast.pos()
        assert new_pos != original_pos 