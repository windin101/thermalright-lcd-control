# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Collapsible Widget Palette for drag-and-drop widget creation"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QSize
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont, QIcon


class PaletteItem(QFrame):
    """A draggable item in the widget palette representing a widget type"""
    
    def __init__(self, widget_type: str, display_name: str, icon_text: str = None, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.display_name = display_name
        self.icon_text = icon_text or display_name[:2].upper()
        
        self.setFixedSize(70, 60)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip(f"Drag to add: {display_name}")
        self._drag_start_pos = None
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Icon area
        self.icon_label = QLabel(self.icon_text)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(40, 28)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # Name label
        self.name_label = QLabel(self.display_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 9px; color: #2c3e50;")
        self.name_label.setWordWrap(True)
        
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self.name_label, 0, Qt.AlignCenter)
    
    def _apply_style(self):
        self.setStyleSheet("""
            PaletteItem {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
            PaletteItem:hover {
                background-color: #f5f6fa;
                border-color: #3498db;
            }
        """)
    
    def set_icon_color(self, color: str):
        """Set the icon background color"""
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if self._drag_start_pos is None:
            return
        
        # Check if we've moved enough to start a drag
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return
        
        try:
            # Create drag object
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.widget_type)
            mime_data.setData("application/x-widget-type", self.widget_type.encode())
            drag.setMimeData(mime_data)
            
            # Create drag pixmap - use simple colored rectangle instead of rendering
            pixmap = QPixmap(60, 50)
            pixmap.fill(QColor(52, 152, 219, 180))  # Semi-transparent blue
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(30, 25))  # Center of pixmap
            
            # Execute drag
            self.setCursor(Qt.ClosedHandCursor)
            drag.exec(Qt.CopyAction)
            self.setCursor(Qt.OpenHandCursor)
        except Exception as e:
            print(f"Drag error: {e}")
            self.setCursor(Qt.OpenHandCursor)


class WidgetPaletteSection(QWidget):
    """A section within the palette containing related widgets"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._items = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Section title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Items grid
        self.grid_widget = QWidget()
        self.grid_layout = QHBoxLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(6)
        self.grid_layout.addStretch()
        
        layout.addWidget(self.grid_widget)
    
    def add_item(self, widget_type: str, display_name: str, icon_text: str = None, color: str = "#3498db"):
        """Add a palette item to this section"""
        item = PaletteItem(widget_type, display_name, icon_text)
        item.set_icon_color(color)
        self._items.append(item)
        
        # Insert before the stretch
        self.grid_layout.insertWidget(self.grid_layout.count() - 1, item)
        return item


class WidgetPalette(QWidget):
    """Collapsible widget palette with draggable widget items organized by category"""
    
    # Signal emitted when a widget should be added at a position
    widget_requested = Signal(str, int, int)  # widget_type, x, y
    
    def __init__(self, parent=None, expand_upward=False):
        super().__init__(parent)
        self._expanded = False
        self._expand_upward = expand_upward
        self._setup_ui()
        self._populate_widgets()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header bar (always visible)
        self.header = QWidget()
        self.header.setFixedHeight(32)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
        """)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        # Expand/collapse indicator - different arrow for upward expansion
        if self._expand_upward:
            self.toggle_label = QLabel("▲")
        else:
            self.toggle_label = QLabel("▶")
        self.toggle_label.setStyleSheet("color: #3498db; font-size: 10px; font-weight: bold;")
        
        # Title
        title_label = QLabel("Widget Palette")
        title_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 12px;")
        
        # Hint
        hint_label = QLabel("Drag widgets to preview")
        hint_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        header_layout.addWidget(self.toggle_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(hint_label)
        
        # Content area (collapsible)
        self.content = QWidget()
        self.content.setVisible(False)
        
        # Style depends on expansion direction
        if self._expand_upward:
            self.content.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    border: 1px solid #dcdde1;
                    border-bottom: none;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
            """)
        else:
            self.content.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    border: 1px solid #dcdde1;
                    border-top: none;
                    border-bottom-left-radius: 6px;
                    border-bottom-right-radius: 6px;
                }
            """)
        
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(12, 8, 12, 12)
        content_layout.setSpacing(12)
        
        # Scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(180)
        
        self.sections_widget = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_widget)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(12)
        
        scroll.setWidget(self.sections_widget)
        content_layout.addWidget(scroll)
        
        # Add widgets in order based on expansion direction
        if self._expand_upward:
            # Content first (above), then header (below)
            main_layout.addWidget(self.content)
            main_layout.addWidget(self.header)
        else:
            # Header first (above), then content (below)
            main_layout.addWidget(self.header)
            main_layout.addWidget(self.content)
        
        # Connect header click
        self.header.mousePressEvent = self._on_header_click
    
    def _on_header_click(self, event):
        self.toggle_expanded()
    
    def toggle_expanded(self):
        """Toggle the expanded/collapsed state"""
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        
        # Set arrows based on direction
        if self._expand_upward:
            self.toggle_label.setText("▼" if self._expanded else "▲")
        else:
            self.toggle_label.setText("▲" if self._expanded else "▼")
        
        # Update header style for expanded state
        if self._expanded:
            if self._expand_upward:
                # Content is above header, round bottom of header
                self.header.setStyleSheet("""
                    QWidget {
                        background-color: #ecf0f1;
                        border: 1px solid #dcdde1;
                        border-top: none;
                        border-top-left-radius: 0px;
                        border-top-right-radius: 0px;
                        border-bottom-left-radius: 6px;
                        border-bottom-right-radius: 6px;
                    }
                """)
            else:
                # Content is below header, round top of header
                self.header.setStyleSheet("""
                    QWidget {
                        background-color: #ecf0f1;
                        border: 1px solid #dcdde1;
                        border-bottom: none;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    }
                """)
        else:
            self.header.setStyleSheet("""
                QWidget {
                    background-color: #ecf0f1;
                    border: 1px solid #dcdde1;
                    border-radius: 6px;
                }
            """)
    
    def _populate_widgets(self):
        """Populate the palette with all available widget types"""
        
        # Text Widgets Section
        text_section = WidgetPaletteSection("Text & Time")
        text_section.add_item("date", "Date", "📅", "#9b59b6")
        text_section.add_item("time", "Time", "🕐", "#9b59b6")
        text_section.add_item("free_text", "Text", "Aa", "#8e44ad")
        self.sections_layout.addWidget(text_section)
        
        # CPU Metrics Section
        cpu_section = WidgetPaletteSection("CPU Metrics")
        cpu_section.add_item("cpu_usage", "Usage", "%", "#3498db")
        cpu_section.add_item("cpu_temperature", "Temp", "°C", "#e74c3c")
        cpu_section.add_item("cpu_frequency", "Freq", "Hz", "#2ecc71")
        cpu_section.add_item("cpu_name", "Name", "CPU", "#34495e")
        self.sections_layout.addWidget(cpu_section)
        
        # GPU Metrics Section
        gpu_section = WidgetPaletteSection("GPU Metrics")
        gpu_section.add_item("gpu_usage", "Usage", "%", "#3498db")
        gpu_section.add_item("gpu_temperature", "Temp", "°C", "#e74c3c")
        gpu_section.add_item("gpu_frequency", "Freq", "Hz", "#2ecc71")
        gpu_section.add_item("gpu_name", "Name", "GPU", "#34495e")
        self.sections_layout.addWidget(gpu_section)
        
        # Memory Section
        mem_section = WidgetPaletteSection("Memory")
        mem_section.add_item("ram_percent", "RAM %", "RAM", "#f39c12")
        mem_section.add_item("ram_total", "RAM GB", "GB", "#f39c12")
        mem_section.add_item("gpu_mem_percent", "VRAM %", "VRM", "#e67e22")
        mem_section.add_item("gpu_mem_total", "VRAM GB", "GB", "#e67e22")
        self.sections_layout.addWidget(mem_section)
        
        # Graph Widgets Section
        graph_section = WidgetPaletteSection("Graphs")
        graph_section.add_item("bar_graph", "Bar", "▬", "#1abc9c")
        graph_section.add_item("arc_graph", "Arc", "◔", "#16a085")
        self.sections_layout.addWidget(graph_section)
        
        # Shape Widgets Section
        shape_section = WidgetPaletteSection("Shapes")
        shape_section.add_item("shape_rectangle", "Rect", "▢", "#95a5a6")
        shape_section.add_item("shape_rounded_rect", "Rounded", "▢", "#7f8c8d")
        shape_section.add_item("shape_circle", "Circle", "○", "#9b59b6")
        shape_section.add_item("shape_ellipse", "Ellipse", "⬭", "#8e44ad")
        shape_section.add_item("shape_line", "Line", "─", "#34495e")
        shape_section.add_item("shape_triangle", "Triangle", "△", "#e67e22")
        shape_section.add_item("shape_arrow", "Arrow", "→", "#27ae60")
        self.sections_layout.addWidget(shape_section)
        
        # Add stretch at bottom
        self.sections_layout.addStretch()
    
    def is_expanded(self) -> bool:
        return self._expanded
