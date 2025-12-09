# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Themes tab for displaying and selecting theme configurations
"""

import glob
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QGridLayout, QPushButton, QMessageBox,
                               QSpacerItem, QSizePolicy)

from thermalright_lcd_control.gui.widgets.thumbnail_widget import ThumbnailWidget
from thermalright_lcd_control.common.logging_config import get_gui_logger
from thermalright_lcd_control.device_controller.display.config_loader import ConfigLoader
from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator


class ThemesTab(QWidget):
    """Tab widget for displaying theme files"""

    theme_selected = Signal(str)  # Signal emitted with selected theme path

    def __init__(self, themes_dir: str, dev_width: int, dev_height: int):
        super().__init__()

        self.logger = get_gui_logger()
        self.themes_dir = Path(Path.cwd(), themes_dir)
        self.thumbnails = []
        self.dev_width = dev_width
        self.dev_height = dev_height
        self.setup_ui()
        self.load_themes()

    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Available Themes")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_themes)
        refresh_btn.setMaximumWidth(100)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Scrollable area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.thumbnails_widget = QWidget()
        self.thumbnails_layout = QGridLayout(self.thumbnails_widget)
        self.thumbnails_layout.setSpacing(10)
        self.thumbnails_layout.setContentsMargins(10, 10, 10, 10)
        
        # Set column stretch to prevent horizontal expansion
        for i in range(4):
            self.thumbnails_layout.setColumnStretch(i, 0)

        scroll_area.setWidget(self.thumbnails_widget)
        main_layout.addWidget(scroll_area)

    def load_themes(self):
        """Load theme files from themes directory"""
        self.cleanup_thumbnails()

        if not self.themes_dir.exists():
            self.themes_dir.mkdir(parents=True, exist_ok=True)
            return

        # Find all YAML files
        yaml_files = []
        for pattern in ['*.yaml', '*.yml']:
            yaml_files.extend(self.themes_dir.glob(pattern))

        if not yaml_files:
            # Show "no themes" message
            no_themes_label = QLabel("No theme files found in themes directory")
            no_themes_label.setAlignment(Qt.AlignCenter)
            no_themes_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 50px;")
            self.thumbnails_layout.addWidget(no_themes_label, 0, 0)
            return

        # Sort by modification date (most recent first)
        yaml_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Create thumbnails
        row, col = 0, 0
        max_cols = 4  # Number of thumbnails per row (reduced for better fit)

        for yaml_file in yaml_files:
            try:
                theme_name = self.get_theme_display_name(yaml_file)
                
                # Generate full theme preview
                preview_pixmap = self.generate_theme_preview(yaml_file)
                
                # Create thumbnail widget
                thumbnail_widget = ThumbnailWidget("", theme_name)
                
                if preview_pixmap:
                    # Use the full theme preview
                    thumbnail_widget.set_pixmap(preview_pixmap)
                else:
                    # Fallback to background-only if preview generation fails
                    background_path, background_type = self.get_theme_background_info(yaml_file)
                    thumbnail_path = self.get_thumbnail_path(background_path, background_type)
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        thumbnail_widget = ThumbnailWidget(thumbnail_path, theme_name)

                # Add special styling for theme thumbnails
                thumbnail_widget.setStyleSheet(thumbnail_widget.styleSheet() + """
                    QWidget {
                        border: 2px solid #3498db;
                    }
                    QWidget:hover {
                        border: 3px solid #2980b9;
                        background-color: #ebf5fb;
                    }
                """)

                # Create a container using absolute positioning (no layout)
                container = QWidget()
                container.setFixedSize(120, 100)
                
                # Position thumbnail inside container
                thumbnail_widget.setParent(container)
                thumbnail_widget.setGeometry(0, 0, 120, 100)
                thumbnail_widget.clicked.connect(
                    lambda path, theme_path=str(yaml_file): self.on_theme_selected(theme_path))
                
                # Add delete button as overlay in top-right corner
                delete_btn = QPushButton("X", container)
                delete_btn.setFixedSize(20, 20)
                delete_btn.setMinimumSize(20, 20)
                delete_btn.setMaximumSize(20, 20)
                delete_btn.move(96, 2)
                delete_btn.setToolTip(f"Delete {theme_name}")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(231, 76, 60, 0.9);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 0px;
                        margin: 0px;
                        min-width: 20px;
                        max-width: 20px;
                        min-height: 20px;
                        max-height: 20px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                delete_btn.clicked.connect(
                    lambda checked, path=str(yaml_file), name=theme_name: self.delete_theme(path, name))
                delete_btn.raise_()

                self.thumbnails_layout.addWidget(container, row, col)
                self.thumbnails.append(container)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            except Exception as e:
                self.logger.error(f"Error loading theme {yaml_file}: {e}")
                continue

        # Add spacer to push everything to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.thumbnails_layout.addItem(spacer, row + 1, 0, 1, max_cols)

    def get_theme_display_name(self, yaml_file: Path) -> str:
        """Get display name for theme file"""
        # Remove extension and clean up filename
        name = yaml_file.stem

        # Replace underscores with spaces and capitalize
        name = name.replace('_', ' ').replace('-', ' ')
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def get_theme_background_info(self, yaml_file: Path) -> tuple[str, str]:
        """Extract background path and type from theme YAML file"""
        try:
            # Load theme configuration
            config_loader = ConfigLoader()
            theme_config = config_loader.load_config(str(yaml_file), self.dev_width, self.dev_height)

            # Get background path and type
            background_path = theme_config.background_path
            background_type = theme_config.background_type.value

            return background_path, background_type

        except Exception as e:
            self.logger.error(f"Error reading theme config {yaml_file}: {e}")
            return "", "image"

    def get_thumbnail_path(self, background_path: str, background_type: str) -> str:
        """Get the actual file path to use for thumbnail generation"""
        if not background_path:
            return ""

        # If it's an image_collection, find the first image in the directory
        if background_type == "image_collection":
            if os.path.isdir(background_path):
                return self.get_first_image_from_collection(background_path)
            else:
                self.logger.warning(f"Background path is not a directory: {background_path}")
                return ""
        else:
            # For other types (image, video, gif), use the path directly
            return background_path

    def get_first_image_from_collection(self, collection_path: str) -> str:
        """Get the first image file from an image collection directory"""
        try:
            # Search for all images in the folder (same logic as frame_manager.py)
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
            image_files = []

            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(collection_path, ext)))
                image_files.extend(glob.glob(os.path.join(collection_path, ext.upper())))

            if image_files:
                image_files.sort()  # Alphabetical sort
                return image_files[0]  # Return first image
            else:
                self.logger.warning(f"No images found in collection directory: {collection_path}")
                return ""

        except Exception as e:
            self.logger.error(f"Error getting first image from collection {collection_path}: {e}")
            return ""

    def on_theme_selected(self, theme_path: str):
        """Handle theme selection"""
        self.theme_selected.emit(theme_path)

    def generate_theme_preview(self, yaml_file: Path) -> 'QPixmap | None':
        """Generate a full preview image of the theme including all elements"""
        try:
            from PySide6.QtGui import QPixmap, QImage
            
            # Load the full theme configuration
            config_loader = ConfigLoader()
            theme_config = config_loader.load_config(str(yaml_file), self.dev_width, self.dev_height)
            
            # Create a DisplayGenerator with the theme config
            generator = DisplayGenerator(theme_config)
            
            # Generate sample metrics for preview
            sample_metrics = {
                'cpu_temperature': 45,
                'gpu_temperature': 55,
                'cpu_usage': 25,
                'gpu_usage': 40,
                'cpu_frequency': 3600,
                'gpu_frequency': 1800
            }
            
            # Generate a frame with the sample metrics (no rotation for thumbnail)
            pil_image = generator.generate_frame_with_metrics(sample_metrics, apply_rotation=False)
            
            # Clean up the generator
            generator.cleanup()
            
            # Convert PIL image to QPixmap
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            width, height = pil_image.size
            image_data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(image_data, width, height, width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            return pixmap
            
        except Exception as e:
            self.logger.error(f"Error generating theme preview for {yaml_file}: {e}")
            return None
        """Handle theme selection"""
        self.theme_selected.emit(theme_path)

    def delete_theme(self, theme_path: str, theme_name: str):
        """Delete a theme file after confirmation"""
        reply = QMessageBox.question(
            self,
            "Delete Theme",
            f"Are you sure you want to delete the theme '{theme_name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                theme_file = Path(theme_path)
                if theme_file.exists():
                    theme_file.unlink()
                    self.logger.info(f"Deleted theme: {theme_path}")
                    self.refresh_themes()
                else:
                    QMessageBox.warning(self, "Error", "Theme file not found.")
            except Exception as e:
                self.logger.error(f"Error deleting theme {theme_path}: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete theme:\n{str(e)}")

    def get_first_theme_path(self) -> str:
        """Get the path of the first available theme"""
        try:
            if not self.themes_dir.exists():
                return ""

            # Find all YAML files
            yaml_files = []
            for pattern in ['*.yaml', '*.yml']:
                yaml_files.extend(self.themes_dir.glob(pattern))

            if not yaml_files:
                return ""

            # Sort by modification date (most recent first)
            yaml_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            return str(yaml_files[0])  # Return first theme

        except Exception as e:
            self.logger.error(f"Error getting first theme path: {e}")
            return ""

    def auto_load_first_theme(self):
        """Automatically load and emit the first available theme"""
        first_theme_path = self.get_first_theme_path()
        if first_theme_path:
            self.theme_selected.emit(first_theme_path)
            return True
        return False

    def refresh_themes(self):
        """Refresh the themes list"""
        self.load_themes()

    def cleanup_thumbnails(self):
        """Clean up existing thumbnails"""
        for thumbnail in self.thumbnails:
            if hasattr(thumbnail, 'cleanup_video'):
                thumbnail.cleanup_video()
            thumbnail.setParent(None)
            thumbnail.deleteLater()
        self.thumbnails.clear()

        # Clear layout
        while self.thumbnails_layout.count():
            child = self.thumbnails_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup_thumbnails()
        super().closeEvent(event)
