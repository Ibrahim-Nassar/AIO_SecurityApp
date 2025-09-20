"""Tests for design tokens and theme system."""

import pytest
from PySide6.QtGui import QColor

from qt_app.ui import theme


class TestThemeTokens:
    """Test design tokens exist and return valid values."""
    
    def test_color_tokens_exist(self):
        """Test that all required color tokens exist."""
        # Core colors
        assert hasattr(theme, 'COLOR_BG')
        assert hasattr(theme, 'COLOR_BG_CARD')
        assert hasattr(theme, 'COLOR_TEXT')
        assert hasattr(theme, 'COLOR_TEXT_MUTED')
        assert hasattr(theme, 'COLOR_PRIMARY')
        assert hasattr(theme, 'COLOR_PRIMARY_HOVER')
        assert hasattr(theme, 'COLOR_SUCCESS')
        assert hasattr(theme, 'COLOR_WARNING')
        assert hasattr(theme, 'COLOR_ERROR')
        assert hasattr(theme, 'COLOR_BORDER')
        assert hasattr(theme, 'COLOR_SHADOW')
        
        # Toast-specific colors
        assert hasattr(theme, 'COLOR_TOAST_INFO_BG')
        assert hasattr(theme, 'COLOR_TOAST_INFO_BORDER')
        assert hasattr(theme, 'COLOR_TOAST_SUCCESS_BORDER')
        assert hasattr(theme, 'COLOR_TOAST_WARNING_BORDER')
        assert hasattr(theme, 'COLOR_TOAST_ERROR_BORDER')
        
        # Overlay colors
        assert hasattr(theme, 'COLOR_OVERLAY_BG')
        assert hasattr(theme, 'COLOR_OVERLAY_TEXT')
    
    def test_color_tokens_are_qcolor(self):
        """Test that color tokens return QColor instances."""
        color_tokens = [
            theme.COLOR_BG, theme.COLOR_BG_CARD, theme.COLOR_TEXT,
            theme.COLOR_TEXT_MUTED, theme.COLOR_PRIMARY, theme.COLOR_PRIMARY_HOVER,
            theme.COLOR_SUCCESS, theme.COLOR_WARNING, theme.COLOR_ERROR,
            theme.COLOR_BORDER, theme.COLOR_SHADOW, theme.COLOR_TOAST_INFO_BG,
            theme.COLOR_TOAST_INFO_BORDER, theme.COLOR_TOAST_SUCCESS_BORDER,
            theme.COLOR_TOAST_WARNING_BORDER, theme.COLOR_TOAST_ERROR_BORDER,
            theme.COLOR_OVERLAY_BG, theme.COLOR_OVERLAY_TEXT
        ]
        
        for color in color_tokens:
            assert isinstance(color, QColor), f"Color token {color} is not a QColor"
            assert color.isValid(), f"Color token {color} is not valid"
    
    def test_spacing_tokens_exist(self):
        """Test that spacing tokens exist and have valid values."""
        assert hasattr(theme, 'SPACE_0')
        assert hasattr(theme, 'SPACE_1')
        assert hasattr(theme, 'SPACE_2')
        assert hasattr(theme, 'SPACE_3')
        assert hasattr(theme, 'SPACE_4')
        
        assert theme.SPACE_0 == 0
        assert theme.SPACE_1 == 4
        assert theme.SPACE_2 == 8
        assert theme.SPACE_3 == 12
        assert theme.SPACE_4 == 16
    
    def test_radius_tokens_exist(self):
        """Test that radius tokens exist and have valid values."""
        assert hasattr(theme, 'RADIUS_SM')
        assert hasattr(theme, 'RADIUS_MD')
        assert hasattr(theme, 'RADIUS_LG')
        
        assert theme.RADIUS_SM == 4
        assert theme.RADIUS_MD == 8
        assert theme.RADIUS_LG == 12
    
    def test_font_tokens_exist(self):
        """Test that font size tokens exist and have valid values."""
        assert hasattr(theme, 'FONT_SM')
        assert hasattr(theme, 'FONT_MD')
        assert hasattr(theme, 'FONT_LG')
        
        assert theme.FONT_SM == 11
        assert theme.FONT_MD == 13
        assert theme.FONT_LG == 15
    
    def test_color_hex_helper(self):
        """Test the color_hex helper function."""
        assert hasattr(theme, 'color_hex')
        
        # Test with a known color
        red = QColor(255, 0, 0)
        assert theme.color_hex(red) == "#ff0000"
        
        # Test with theme colors
        assert isinstance(theme.color_hex(theme.COLOR_PRIMARY), str)
        assert theme.color_hex(theme.COLOR_PRIMARY).startswith("#")
    
    def test_toast_colors_match_expected_values(self):
        """Test that toast colors match the exact expected values."""
        # Success should be #108A48
        assert theme.COLOR_SUCCESS.red() == 16
        assert theme.COLOR_SUCCESS.green() == 138
        assert theme.COLOR_SUCCESS.blue() == 72
        
        # Warning should be #C27803
        assert theme.COLOR_WARNING.red() == 194
        assert theme.COLOR_WARNING.green() == 120
        assert theme.COLOR_WARNING.blue() == 3
        
        # Error should be #B22222
        assert theme.COLOR_ERROR.red() == 178
        assert theme.COLOR_ERROR.green() == 34
        assert theme.COLOR_ERROR.blue() == 34


class TestThemeQSS:
    """Test QSS generation includes required button classes."""
    
    def test_qss_includes_button_classes(self):
        """Test that _qss() includes PrimaryButton, SecondaryButton, DestructiveButton."""
        qss = theme._qss()
        
        assert "PrimaryButton" in qss
        assert "SecondaryButton" in qss
        assert "DestructiveButton" in qss
    
    def test_qss_uses_color_hex_helper(self):
        """Test that QSS generation uses color_hex helper instead of direct .name() calls."""
        qss = theme._qss()
        
        # Should contain hex colors from our tokens
        assert theme.color_hex(theme.COLOR_PRIMARY) in qss
        assert theme.color_hex(theme.COLOR_BG) in qss
        assert theme.color_hex(theme.COLOR_TEXT) in qss
    
    def test_no_hardcoded_hex_in_qss(self):
        """Test that QSS doesn't contain hardcoded hex values."""
        qss = theme._qss()
        
        # Should not contain old hardcoded values
        assert "#E7F4F4" not in qss  # Should use COLOR_PRIMARY_LIGHT token
        assert "#D6ECEC" not in qss  # Should use COLOR_PRIMARY_LIGHTER token
        assert "#F3F8FA" not in qss  # Should use COLOR_HOVER_SECONDARY token 