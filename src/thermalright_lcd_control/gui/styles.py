# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Modern stylesheet for Thermalright LCD Control GUI
"""

from PySide6.QtWidgets import QApplication, QComboBox, QSpinBox, QDoubleSpinBox
from PySide6.QtGui import QPalette, QColor


def _create_input_palette():
    """Create a palette suitable for input widgets (spinbox, combobox)."""
    palette = QPalette()
    
    # Base colors for input widgets
    palette.setColor(QPalette.Window, QColor(248, 249, 250))       # Light grey for button area
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))      # Dark text
    palette.setColor(QPalette.Base, QColor(255, 255, 255))         # White input background
    palette.setColor(QPalette.AlternateBase, QColor(245, 246, 250))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))            # Dark text in inputs
    palette.setColor(QPalette.Button, QColor(248, 249, 250))       # Light button background
    palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))      # Dark button text (for arrows)
    palette.setColor(QPalette.Highlight, QColor(52, 152, 219))     # Blue selection
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Light, QColor(255, 255, 255))        # For 3D effects
    palette.setColor(QPalette.Dark, QColor(160, 160, 160))         # For 3D effects/arrows
    palette.setColor(QPalette.Mid, QColor(200, 200, 200))          # For borders
    palette.setColor(QPalette.Shadow, QColor(100, 100, 100))       # For shadows/arrows
    
    # Disabled state
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(149, 165, 166))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(149, 165, 166))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(240, 240, 240))
    
    return palette


def setup_application_palette(app: QApplication):
    """Set up the application palette for proper widget colors with Fusion style."""
    palette = app.palette()
    
    # Base colors
    palette.setColor(QPalette.Window, QColor(245, 246, 250))       # Light grey background
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))      # Dark text
    palette.setColor(QPalette.Base, QColor(255, 255, 255))         # White input backgrounds
    palette.setColor(QPalette.AlternateBase, QColor(245, 246, 250))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))            # Dark text in inputs
    palette.setColor(QPalette.Button, QColor(248, 249, 250))       # Light button background
    palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))      # Dark button text
    palette.setColor(QPalette.Highlight, QColor(52, 152, 219))     # Blue selection
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # White text on selection
    palette.setColor(QPalette.Light, QColor(255, 255, 255))
    palette.setColor(QPalette.Dark, QColor(160, 160, 160))
    palette.setColor(QPalette.Mid, QColor(200, 200, 200))
    palette.setColor(QPalette.Shadow, QColor(100, 100, 100))
    
    # Disabled colors
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(149, 165, 166))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(149, 165, 166))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(149, 165, 166))
    
    app.setPalette(palette)


def style_input_widget(widget):
    """Apply proper styling to input widgets (QComboBox, QSpinBox, QDoubleSpinBox).
    
    This overrides stylesheet inheritance by setting the palette directly on the widget,
    ensuring proper colors and visible arrows/buttons.
    """
    # Clear any inherited stylesheet
    widget.setStyleSheet("")
    
    # Apply input palette
    widget.setPalette(_create_input_palette())
    
    # For combobox, also style the popup view
    if isinstance(widget, QComboBox):
        view = widget.view()
        if view:
            view.setStyleSheet("")
            view.setPalette(_create_input_palette())


def fix_combobox_popup(combobox):
    """Fix combobox popup colors for proper visibility on all platforms.
    
    Alias for style_input_widget for backwards compatibility.
    """
    style_input_widget(combobox)


MODERN_STYLESHEET = """
/* ===== Global Styles ===== */
QMainWindow {
    background-color: #f5f6fa;
}

QWidget {
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}

/* ===== Group Boxes ===== */
QGroupBox {
    font-weight: bold;
    font-size: 12px;
    color: #2c3e50;
    border: 1px solid #dcdde1;
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px 6px 6px 6px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: #ffffff;
    color: #2c3e50;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1c5980;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

/* Secondary/Flat buttons */
QPushButton[flat="true"], QPushButton#secondaryButton {
    background-color: transparent;
    color: #3498db;
    border: 1px solid #3498db;
}

QPushButton[flat="true"]:hover, QPushButton#secondaryButton:hover {
    background-color: rgba(52, 152, 219, 0.1);
}

/* ===== Tabs ===== */
QTabWidget::pane {
    border: 1px solid #dcdde1;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background-color: #ecf0f1;
    color: #7f8c8d;
    border: 1px solid #dcdde1;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 10px 20px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover:!selected {
    background-color: #d5dbdb;
    color: #2c3e50;
}

/* ===== Inputs ===== */
/* Only style QLineEdit - let QSpinBox and QComboBox use native Fusion styling */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #dcdde1;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
    color: #2c3e50;
}

QLineEdit:focus {
    border: 2px solid #3498db;
    padding: 5px 9px;
}

QLineEdit:disabled {
    background-color: #ecf0f1;
    color: #95a5a6;
}

/* ===== Sliders ===== */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #dcdde1;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #3498db;
    border: none;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #2980b9;
}

QSlider::sub-page:horizontal {
    background-color: #3498db;
    border-radius: 3px;
}

/* ===== Checkboxes ===== */
QCheckBox {
    spacing: 8px;
    color: #2c3e50;
    margin: 2px 0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #bdc3c7;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border-color: #3498db;
    image: none;
}

QCheckBox::indicator:hover {
    border-color: #3498db;
}

/* ===== Labels ===== */
QLabel {
    color: #2c3e50;
}

/* ===== Scroll Areas ===== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    min-height: 30px;
    border-radius: 4px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #f5f6fa;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #bdc3c7;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== Frames ===== */
QFrame#previewFrame {
    border: 2px solid #bdc3c7;
    border-radius: 6px;
    background-color: #ecf0f1;
}

/* ===== Font Combo Box ===== */
QFontComboBox {
    background-color: #ffffff;
    border: 1px solid #dcdde1;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
}

QFontComboBox:focus {
    border: 2px solid #3498db;
}

/* ===== Tool Tips ===== */
QToolTip {
    background-color: #2c3e50;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
}

/* ===== Message Box ===== */
QMessageBox {
    background-color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


# Alternative dark theme (for future use)
DARK_STYLESHEET = """
/* ===== Global Styles ===== */
QMainWindow {
    background-color: #1a1a2e;
}

QWidget {
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
    color: #eaeaea;
}

/* ===== Group Boxes ===== */
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    color: #eaeaea;
    border: 1px solid #3a3a5a;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    background-color: #16213e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #16213e;
    color: #eaeaea;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #0f4c75;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #3282b8;
}

QPushButton:pressed {
    background-color: #1b262c;
}

QPushButton:disabled {
    background-color: #3a3a5a;
    color: #6a6a8a;
}

/* ===== Tabs ===== */
QTabWidget::pane {
    border: 1px solid #3a3a5a;
    border-radius: 8px;
    background-color: #16213e;
    top: -1px;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #8a8aaa;
    border: 1px solid #3a3a5a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 10px 20px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #16213e;
    color: #eaeaea;
    border-bottom: 2px solid #3282b8;
}

QTabBar::tab:hover:!selected {
    background-color: #252545;
    color: #eaeaea;
}

/* ===== Inputs ===== */
QLineEdit {
    background-color: #1a1a2e;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
    color: #eaeaea;
}

QLineEdit:focus {
    border: 2px solid #3282b8;
    padding: 5px 9px;
}

/* ===== Sliders ===== */
QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #3a3a5a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #3282b8;
    border: none;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background-color: #3282b8;
    border-radius: 3px;
}

/* ===== Checkboxes ===== */
QCheckBox {
    spacing: 8px;
    color: #eaeaea;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #5a5a7a;
    border-radius: 4px;
    background-color: #1a1a2e;
}

QCheckBox::indicator:checked {
    background-color: #3282b8;
    border-color: #3282b8;
}

/* ===== Labels ===== */
QLabel {
    color: #eaeaea;
}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3a3a5a;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a5a7a;
}

QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #3a3a5a;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

/* ===== Tool Tips ===== */
QToolTip {
    background-color: #0f4c75;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
}
"""
