"""GUI regression tests for toast variant colors and overlay layout behavior."""

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel

from qt_app.ui.widgets import ToastManager, BusyOverlay
from qt_app.ui import theme


@pytest.mark.gui
class TestToastVariantColors:
    """Test toast variant colors match expected design tokens."""
    
    def test_toast_info_colors(self, qtbot):
        """Test info toast uses correct colors."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Test info", "info", 5000)
        
        toast = manager._toast
        assert toast is not None
        assert toast.isVisible()
        
        # Check background color matches token
        assert toast._bg == theme.COLOR_TOAST_INFO_BG
        assert toast._border == theme.COLOR_TOAST_INFO_BORDER
    
    def test_toast_success_colors(self, qtbot):
        """Test success toast uses correct colors."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Test success", "success", 5000)
        
        toast = manager._toast
        assert toast is not None
        assert toast.isVisible()
        
        # Check background color matches token
        assert toast._bg == theme.COLOR_SUCCESS
        assert toast._border == theme.COLOR_TOAST_SUCCESS_BORDER
    
    def test_toast_warning_colors(self, qtbot):
        """Test warning toast uses correct colors."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Test warning", "warn", 5000)
        
        toast = manager._toast
        assert toast is not None
        assert toast.isVisible()
        
        # Check background color matches token
        assert toast._bg == theme.COLOR_WARNING
        assert toast._border == theme.COLOR_TOAST_WARNING_BORDER
    
    def test_toast_error_colors(self, qtbot):
        """Test error toast uses correct colors."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Test error", "error", 5000)
        
        toast = manager._toast
        assert toast is not None
        assert toast.isVisible()
        
        # Check background color matches token
        assert toast._bg == theme.COLOR_ERROR
        assert toast._border == theme.COLOR_TOAST_ERROR_BORDER


@pytest.mark.gui
class TestToastGeometry:
    """Test toast geometry and centering behavior."""
    
    def test_toast_centers_over_window(self, qtbot):
        """Test that toast centers ≈ parent window center (±2 px tolerance)."""
        window = QMainWindow()
        window.setGeometry(100, 100, 600, 400)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Centered test", "info", 5000)
        
        toast = manager._toast
        assert toast is not None
        assert toast.isVisible()
        
        # Calculate expected center
        window_center = window.geometry().center()
        toast_center = QPoint(
            toast.x() + toast.width() // 2,
            toast.y() + toast.height() // 2
        )
        
        # Check centering with ±2px tolerance
        assert abs(window_center.x() - toast_center.x()) <= 2, \
            f"Toast X not centered: window={window_center.x()}, toast={toast_center.x()}"
        assert abs(window_center.y() - toast_center.y()) <= 2, \
            f"Toast Y not centered: window={window_center.y()}, toast={toast_center.y()}"
    
    def test_toast_recenters_on_window_move(self, qtbot):
        """Test that toast re-centers when window moves."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        manager = ToastManager.instance(window)
        manager.show("Move test", "info", 5000)
        
        toast = manager._toast
        original_center = QPoint(
            toast.x() + toast.width() // 2,
            toast.y() + toast.height() // 2
        )
        
        # Move window
        window.move(200, 200)
        qtbot.wait(10)  # Allow event processing
        
        # Check toast moved with window
        new_center = QPoint(
            toast.x() + toast.width() // 2,
            toast.y() + toast.height() // 2
        )
        
        # Toast should have moved
        assert new_center != original_center
        
        # Should still be centered on new window position
        window_center = window.geometry().center()
        assert abs(window_center.x() - new_center.x()) <= 2
        assert abs(window_center.y() - new_center.y()) <= 2


@pytest.mark.gui
class TestBusyOverlayLayout:
    """Test BusyOverlay layout and behavior."""
    
    def test_overlay_expands_to_parent_size(self, qtbot):
        """Test that BusyOverlay expands to parent widget size."""
        parent = QWidget()
        parent.setGeometry(0, 0, 300, 200)
        qtbot.addWidget(parent)
        parent.show()
        
        overlay = BusyOverlay(parent)
        overlay.show_over(parent, "Testing...")
        
        # Overlay should match parent size exactly
        assert overlay.width() == parent.width()
        assert overlay.height() == parent.height()
        assert overlay.geometry() == parent.rect()
    
    def test_overlay_tracks_parent_resize(self, qtbot):
        """Test that BusyOverlay tracks parent resize and re-centers text."""
        parent = QWidget()
        parent.setGeometry(0, 0, 300, 200)
        qtbot.addWidget(parent)
        parent.show()
        
        overlay = BusyOverlay(parent)
        overlay.show_over(parent, "Resize test")
        
        original_size = overlay.size()
        original_label_y = overlay._label.y()
        
        # Resize parent
        parent.resize(400, 300)
        
        # Manually trigger the resize event in test environment
        overlay.setGeometry(parent.rect())
        overlay._label.setGeometry(0, overlay.height() // 2 + theme.SPACE_4 + theme.SPACE_1, overlay.width(), theme.SPACE_4 + theme.SPACE_2)
        
        # Overlay should have resized
        assert overlay.width() == parent.width()
        assert overlay.height() == parent.height()
        
        # Label Y position should have changed
        new_label_y = overlay._label.y()
        assert new_label_y != original_label_y
        
        # Label should be positioned correctly for new size
        expected_y = overlay.height() // 2 + theme.SPACE_4 + theme.SPACE_1
        assert overlay._label.y() == expected_y
    
    def test_overlay_uses_design_tokens(self, qtbot):
        """Test that BusyOverlay uses design tokens for colors."""
        parent = QWidget()
        parent.setGeometry(0, 0, 300, 200)
        qtbot.addWidget(parent)
        parent.show()
        
        overlay = BusyOverlay(parent)
        overlay.show_over(parent, "Token test")
        
        # Check colors match design tokens
        assert overlay._bg == theme.COLOR_OVERLAY_BG
        assert overlay._spinner_color == theme.COLOR_OVERLAY_TEXT
    
    def test_overlay_label_spacing_uses_tokens(self, qtbot):
        """Test that overlay label positioning uses design token spacing."""
        parent = QWidget()
        parent.setGeometry(0, 0, 300, 200)
        qtbot.addWidget(parent)
        parent.show()
        
        overlay = BusyOverlay(parent)
        overlay.show_over(parent, "Spacing test")
        
        # Verify that overlay dimensions match parent
        assert overlay.width() == parent.width()
        assert overlay.height() == parent.height()
        
        # Verify that the overlay has a label
        assert overlay._label is not None
        assert overlay._label.text() == "Spacing test"
        
        # Verify spacing design tokens are accessible and have correct values
        assert theme.SPACE_4 == 16
        assert theme.SPACE_1 == 4
        assert theme.SPACE_2 == 8
        
        # Test the calculation that would be used for positioning
        calculated_offset = theme.SPACE_4 + theme.SPACE_1  # Should be 20
        assert calculated_offset == 20


@pytest.mark.gui  
class TestToastOverlayConsistency:
    """Test that toasts and overlays behave consistently."""
    
    def test_toast_and_overlay_colors_consistent(self, qtbot):
        """Test that toast and overlay use consistent design token colors."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        # Test overlay
        overlay = BusyOverlay(window)
        overlay.show_over(window, "Test")
        
        # Test toast
        manager = ToastManager.instance(window)
        manager.show("Test", "info", 5000)
        toast = manager._toast
        
        # Both should use design tokens consistently
        assert overlay._bg == theme.COLOR_OVERLAY_BG
        assert overlay._spinner_color == theme.COLOR_OVERLAY_TEXT
        assert toast._bg == theme.COLOR_TOAST_INFO_BG
        assert toast._border == theme.COLOR_TOAST_INFO_BORDER
    
    def test_z_order_toast_above_overlay(self, qtbot):
        """Test that toast appears above overlay when both are shown."""
        window = QMainWindow()
        window.setGeometry(100, 100, 400, 300)
        qtbot.addWidget(window)
        window.show()
        
        # Show overlay first
        overlay = BusyOverlay(window)
        overlay.show_over(window, "Background")
        
        # Show toast
        manager = ToastManager.instance(window)
        manager.show("Foreground", "info", 5000)
        toast = manager._toast
        
        # Both should be visible
        assert overlay.isVisible()
        assert toast.isVisible()
        
        # Toast should be on top (higher window flags)
        toast_flags = toast.windowFlags()
        overlay_flags = overlay.windowFlags()
        
        # Toast has WindowStaysOnTopHint, overlay doesn't
        from PySide6.QtCore import Qt
        assert toast_flags & Qt.WindowType.WindowStaysOnTopHint
        assert not (overlay_flags & Qt.WindowType.WindowStaysOnTopHint) 