"""
Widget Palette - Main palette showing all available widgets in categorized grid.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QScrollArea, QLineEdit, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .widget_config import (
    WidgetMetadata, get_widgets_by_category, 
    get_widget_metadata, CATEGORY_ORDER
)
from .widget_card import WidgetCard


class WidgetPalette(QWidget):
    """
    Widget palette showing all available widgets in categorized grid.
    
    Features:
    - Categorized sections (CPU, GPU, RAM, System, Text)
    - Grid layout with widget cards
    - Search/filter functionality
    - Expandable/collapsible categories
    """
    
    widgetSelected = Signal(str, dict)  # widget_type, default_properties
    
    def __init__(self, parent=None):
        """Initialize widget palette."""
        super().__init__(parent)
        self.setup_ui()
        self.setup_signals()
    
    def setup_ui(self):
        """Setup palette UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFixedWidth(50)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter widgets...")
        self.search_input.setClearButtonEnabled(True)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        
        # Scroll area for categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Categories container
        self.categories_container = QWidget()
        self.categories_layout = QVBoxLayout(self.categories_container)
        self.categories_layout.setSpacing(15)
        self.categories_layout.setContentsMargins(5, 5, 5, 5)
        
        # Load categories
        self.load_categories()
        
        scroll_area.setWidget(self.categories_container)
        main_layout.addWidget(scroll_area)
        
        # Info label
        info_label = QLabel("Click a widget to add it to the preview area")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Arial", 9))
        info_label.setStyleSheet("color: #888; padding: 5px;")
        main_layout.addWidget(info_label)
    
    def load_categories(self):
        """Load all widget categories."""
        widgets_by_category = get_widgets_by_category()
        
        for category in CATEGORY_ORDER:
            if category in widgets_by_category and widgets_by_category[category]:
                category_section = self.create_category_section(
                    category.value, 
                    widgets_by_category[category]
                )
                self.categories_layout.addWidget(category_section)
        
        # Add stretch at the end
        self.categories_layout.addStretch()
    
    def create_category_section(self, category_name: str, 
                               widgets: list[WidgetMetadata]) -> QGroupBox:
        """
        Create a category section with widget cards.
        
        Args:
            category_name: Name of the category
            widgets: List of widget metadata for this category
            
        Returns:
            QGroupBox containing the category
        """
        # Create group box
        group = QGroupBox(category_name)
        group.setCheckable(True)
        group.setChecked(True)
        
        # Connect toggle signal
        group.toggled.connect(lambda checked: self._on_category_toggled(group, checked))
        
        # Create grid for widget cards
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(10, 15, 10, 10)
        
        # Add widget cards
        self._add_widget_cards_to_grid(grid, widgets)
        
        group.setLayout(grid)
        return group
    
    def _add_widget_cards_to_grid(self, grid: QGridLayout, 
                                 widgets: list[WidgetMetadata]):
        """
        Add widget cards to grid layout.
        
        Args:
            grid: Grid layout to add cards to
            widgets: List of widget metadata
        """
        COLUMNS = 3  # 3 columns in grid
        
        for i, widget_meta in enumerate(widgets):
            row = i // COLUMNS
            col = i % COLUMNS
            
            # Create widget card
            card = WidgetCard(widget_meta)
            card.widgetClicked.connect(self._on_widget_card_clicked)
            
            # Store reference
            if not hasattr(self, '_widget_cards'):
                self._widget_cards = {}
            self._widget_cards[widget_meta.widget_type] = card
            
            # Add to grid
            grid.addWidget(card, row, col, Qt.AlignCenter)
    
    def _on_category_toggled(self, group: QGroupBox, checked: bool):
        """
        Handle category expansion/collapse.
        
        Args:
            group: The category group box
            checked: Whether the group is expanded
        """
        # Show/hide the group contents
        group.setFlat(not checked)
        
        # Update group title style
        if checked:
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        else:
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #444;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
    
    def _on_widget_card_clicked(self, widget_type: str, 
                               default_properties: dict):
        """
        Handle widget card click.
        
        Args:
            widget_type: Type of widget clicked
            default_properties: Default properties for the widget
        """
        # Emit signal to parent
        self.widgetSelected.emit(widget_type, default_properties)
    
    def setup_signals(self):
        """Setup signal connections."""
        self.search_input.textChanged.connect(self._on_search_text_changed)
    
    def _on_search_text_changed(self, text: str):
        """
        Handle search text change - filter widgets.
        
        Args:
            text: Search text
        """
        search_text = text.lower().strip()
        
        if not search_text:
            # Show all widgets
            for card in getattr(self, '_widget_cards', {}).values():
                card.setVisible(True)
            return
        
        # Filter widgets
        for widget_type, card in getattr(self, '_widget_cards', {}).items():
            widget_meta = get_widget_metadata(widget_type)
            
            # Check if search text matches widget name or description
            matches = (
                search_text in widget_meta.display_name.lower() or
                search_text in widget_meta.description.lower() or
                search_text in widget_type.lower()
            )
            
            card.setVisible(matches)
    
    def clear_selection(self):
        """Clear any selection state from widget cards."""
        for card in getattr(self, '_widget_cards', {}).values():
            card.reset_style()
    
    def get_widget_count(self) -> int:
        """Get total number of available widgets."""
        return len(getattr(self, '_widget_cards', {}))