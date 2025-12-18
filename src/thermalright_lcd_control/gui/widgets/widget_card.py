"""
Widget Card - Individual widget card for the palette.
"""
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .widget_config import WidgetMetadata


class WidgetCard(QPushButton):
    """
    Clickable widget card for the palette.
    
    Displays:
    - Icon (colored circle with first letter)
    - Widget name
    - Brief description
    """
    
    widgetClicked = Signal(str, dict)  # widget_type, default_properties
    
    def __init__(self, widget_meta: WidgetMetadata):
        """
        Initialize widget card.
        
        Args:
            widget_meta: Widget metadata from widget_config.py
        """
        super().__init__()
        self.widget_meta = widget_meta
        self.widget_type = widget_meta.widget_type
        self.default_properties = widget_meta.default_properties.copy()
        
        self.setup_ui()
        self.setup_styles()
        self.setup_signals()
    
    def setup_ui(self):
        """Setup card UI layout."""
        # Main container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icon (colored circle with letter)
        icon_label = QLabel(self.widget_meta.icon_letter)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(40, 40)
        
        # Set icon style
        icon_style = f"""
            QLabel {{
                background-color: {self.widget_meta.icon_color};
                color: white;
                border-radius: 20px;
                font-weight: bold;
                font-size: 16px;
                qproperty-alignment: 'AlignCenter';
            }}
        """
        icon_label.setStyleSheet(icon_style)
        
        # Widget name
        name_label = QLabel(self.widget_meta.display_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Description (wrapped)
        desc_label = QLabel(self.widget_meta.description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 8))
        
        # Add widgets to layout
        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(desc_label)
        
        # Set the container as the button's layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(container)
        
        # Set fixed size for consistent grid
        self.setFixedSize(120, 140)
    
    def setup_styles(self):
        """Setup card styles and hover effects."""
        base_style = f"""
            QPushButton {{
                background-color: #2D2D2D;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #3A3A3A;
                border: 1px solid #555;
            }}
            QPushButton:pressed {{
                background-color: #444;
                border: 1px solid #666;
            }}
        """
        self.setStyleSheet(base_style)
        
        # Tooltip
        self.setToolTip(f"Add {self.widget_meta.display_name} widget\n{self.widget_meta.description}")
    
    def setup_signals(self):
        """Connect signals."""
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle card click - emit signal with widget info."""
        self.widgetClicked.emit(self.widget_type, self.default_properties)
        
        # Visual feedback
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #444;
                border: 2px solid {self.widget_meta.icon_color};
                border-radius: 8px;
                padding: 0px;
            }}
        """)
        
        # Reset style after brief highlight
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, self.reset_style)
    
    def reset_style(self):
        """Reset card style after click feedback."""
        self.setup_styles()
    
    def enterEvent(self, event):
        """Handle mouse enter event for hover effect."""
        super().enterEvent(event)
        self.setCursor(Qt.PointingHandCursor)
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)
        self.setCursor(Qt.ArrowCursor)