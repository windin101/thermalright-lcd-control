# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Themes tab for displaying and selecting theme configurations
"""

import glob
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QGridLayout, QPushButton, QMessageBox,
                               QSpacerItem, QSizePolicy, QComboBox)

from thermalright_lcd_control.gui.widgets.thumbnail_widget import ThumbnailWidget
from thermalright_lcd_control.common.logging_config import get_gui_logger
import random

from thermalright_lcd_control.device_controller.display.config_loader import ConfigLoader
from thermalright_lcd_control.device_controller.display.generator import DisplayGenerator


class ThemesTab(QWidget):
    """Tab widget for displaying theme files"""

    theme_selected = Signal(str)  # Signal emitted with selected theme path
    new_theme_requested = Signal()  # Signal emitted when New Theme button is clicked

    def __init__(self, themes_dir: str, dev_width: int, dev_height: int, config: dict = None):
        super().__init__()

        self.logger = get_gui_logger()
        self.config = config or {}
        # Use absolute path if provided, otherwise resolve relative to cwd
        themes_path = Path(themes_dir)
        if themes_path.is_absolute():
            self.themes_dir = themes_path
        else:
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

        # Header with buttons (matching MediaTab style)
        header_layout = QHBoxLayout()

        # New Theme button
        new_theme_btn = QPushButton("+ New Theme")
        new_theme_btn.clicked.connect(self.on_new_theme_clicked)
        new_theme_btn.setMaximumWidth(150)

        # Open Folder button
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self.on_open_folder_clicked)
        open_folder_btn.setMaximumWidth(150)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_themes)
        refresh_btn.setMaximumWidth(150)

        header_layout.addWidget(new_theme_btn)
        header_layout.addWidget(open_folder_btn)
        header_layout.addWidget(refresh_btn)
        header_layout.addStretch()
        
        # Startup mode controls
        startup_label = QLabel("Startup:")
        header_layout.addWidget(startup_label)
        
        self.startup_mode_combo = QComboBox()
        self.startup_mode_combo.addItem("Default Theme", "default")
        self.startup_mode_combo.addItem("Random Theme", "random")
        self.startup_mode_combo.addItem("Last Modified", "last_modified")
        self.startup_mode_combo.setFixedWidth(120)
        self.startup_mode_combo.setToolTip("Choose which theme to load when the app starts")
        # Set current value from config
        current_mode = self.config.get('startup_theme_mode', 'default')
        index = self.startup_mode_combo.findData(current_mode)
        if index >= 0:
            self.startup_mode_combo.setCurrentIndex(index)
        self.startup_mode_combo.currentIndexChanged.connect(self.on_startup_mode_changed)
        header_layout.addWidget(self.startup_mode_combo)
        
        # Default theme selector (only visible when mode is 'default')
        self.default_theme_combo = QComboBox()
        self.default_theme_combo.setFixedWidth(150)
        self.default_theme_combo.setToolTip("Select the default theme to load on startup")
        self.default_theme_combo.currentTextChanged.connect(self.on_default_theme_changed)
        header_layout.addWidget(self.default_theme_combo)
        
        # Show/hide default theme combo based on mode
        self.default_theme_combo.setVisible(current_mode == 'default')

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
        for i in range(3):
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
        
        # Populate the default theme combo
        self._populate_default_theme_combo(yaml_files)

        # Create thumbnails
        row, col = 0, 0
        max_cols = 3  # Number of thumbnails per row

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

                # Create a container using absolute positioning (no layout)
                container = QWidget()
                container.setFixedSize(270, 210)
                
                # Position thumbnail inside container
                thumbnail_widget.setParent(container)
                thumbnail_widget.setGeometry(0, 0, 270, 210)
                thumbnail_widget.clicked.connect(
                    lambda path, theme_path=str(yaml_file): self.on_theme_selected(theme_path))
                
                # Add delete button as overlay in top-right corner
                delete_btn = QPushButton("X", container)
                delete_btn.setFixedSize(20, 20)
                delete_btn.setMinimumSize(20, 20)
                delete_btn.setMaximumSize(20, 20)
                delete_btn.move(246, 2)
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

    def on_new_theme_clicked(self):
        """Handle New Theme button click"""
        self.logger.info("on_new_theme_clicked - emitting new_theme_requested signal")
        self.new_theme_requested.emit()

    def on_startup_mode_changed(self, index):
        """Handle startup mode combo change"""
        mode = self.startup_mode_combo.currentData()
        self.config['startup_theme_mode'] = mode
        self._save_gui_config()
        
        # Show/hide default theme combo based on mode
        self.default_theme_combo.setVisible(mode == 'default')
        self.logger.info(f"Startup theme mode changed to: {mode}")

    def on_default_theme_changed(self, theme_name):
        """Handle default theme combo change"""
        if theme_name:
            # Find the actual filename
            for i in range(self.default_theme_combo.count()):
                if self.default_theme_combo.itemText(i) == theme_name:
                    filename = self.default_theme_combo.itemData(i)
                    if filename:
                        self.config['default_theme'] = filename
                        self._save_gui_config()
                        self.logger.info(f"Default theme set to: {filename}")
                    break

    def _save_gui_config(self):
        """Save the GUI config file with updated settings"""
        import yaml
        try:
            # Find the config file path
            config_path = Path("./resources/gui_config.yaml")
            if not config_path.exists():
                # Try alternate location
                config_path = Path.cwd() / "resources" / "gui_config.yaml"
            
            if config_path.exists():
                # Read existing config
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}
                
                # Update with new values
                existing_config['startup_theme_mode'] = self.config.get('startup_theme_mode', 'default')
                existing_config['default_theme'] = self.config.get('default_theme', '')
                
                # Write back
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(existing_config, f, default_flow_style=False, allow_unicode=True, indent=2)
                
                self.logger.debug(f"Saved GUI config to {config_path}")
            else:
                self.logger.warning(f"GUI config file not found at {config_path}")
        except Exception as e:
            self.logger.error(f"Error saving GUI config: {e}")

    def _populate_default_theme_combo(self, yaml_files):
        """Populate the default theme combo with available themes"""
        self.default_theme_combo.blockSignals(True)
        self.default_theme_combo.clear()
        
        current_default = self.config.get('default_theme', '')
        selected_index = 0
        
        for i, yaml_file in enumerate(yaml_files):
            display_name = self.get_theme_display_name(yaml_file)
            filename = yaml_file.name
            self.default_theme_combo.addItem(display_name, filename)
            
            if filename == current_default:
                selected_index = i
        
        if self.default_theme_combo.count() > 0:
            self.default_theme_combo.setCurrentIndex(selected_index)
        
        self.default_theme_combo.blockSignals(False)

    def on_open_folder_clicked(self):
        """Open the themes folder in the system file manager"""
        import subprocess
        import platform
        
        folder_path = str(self.themes_dir)
        
        try:
            # Ensure the directory exists
            self.themes_dir.mkdir(parents=True, exist_ok=True)
            
            system = platform.system()
            if system == "Linux":
                subprocess.Popen(["xdg-open", folder_path])
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", folder_path])
            elif system == "Windows":
                subprocess.Popen(["explorer", folder_path])
            else:
                self.logger.warning(f"Unsupported platform for opening folder: {system}")
        except Exception as e:
            self.logger.error(f"Error opening folder {folder_path}: {e}")

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
                'gpu_frequency': 1800,
                'cpu_name': 'CPU',
                'gpu_name': 'GPU',
                'ram_total': 32,
                'ram_used': 16,
                'ram_percent': 50,
                'gpu_mem_total': 16,
                'gpu_mem_used': 8,
                'gpu_mem_percent': 50
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
        """Delete a theme file after confirmation, with option to delete associated media"""
        import yaml
        
        # First, extract media paths from the theme
        media_files = []
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_config = yaml.safe_load(f)
            
            display_config = theme_config.get('display', {})
            
            # Get background path
            background_config = display_config.get('background', {})
            bg_path = background_config.get('path')
            if bg_path and os.path.exists(bg_path):
                media_files.append(('Background', bg_path))
            
            # Get foreground path
            foreground_config = display_config.get('foreground', {})
            fg_path = foreground_config.get('path')
            if fg_path:
                # Handle resolution placeholder
                fg_path = fg_path.replace('{resolution}', f'{self.dev_width}{self.dev_height}')
                if os.path.exists(fg_path):
                    media_files.append(('Foreground', fg_path))
        except Exception as e:
            self.logger.error(f"Error reading theme media paths: {e}")
        
        # Build the confirmation message
        if media_files:
            media_list = "\n".join([f"  • {name}: {os.path.basename(path)}" for name, path in media_files])
            message = (f"Are you sure you want to delete the theme '{theme_name}'?\n\n"
                      f"This theme uses the following media files:\n{media_list}\n\n"
                      f"What would you like to do?")
            
            # Create custom dialog with three options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Delete Theme")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Question)
            
            delete_all_btn = msg_box.addButton("Delete Theme && Media", QMessageBox.DestructiveRole)
            delete_theme_btn = msg_box.addButton("Delete Theme Only", QMessageBox.AcceptRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_btn)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            
            if clicked == cancel_btn:
                return
            
            delete_media = (clicked == delete_all_btn)
        else:
            # No media files, simple confirmation
            reply = QMessageBox.question(
                self,
                "Delete Theme",
                f"Are you sure you want to delete the theme '{theme_name}'?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            delete_media = False
        
        # Delete the theme file
        try:
            theme_file = Path(theme_path)
            if theme_file.exists():
                theme_file.unlink()
                self.logger.info(f"Deleted theme: {theme_path}")
                
                # Delete media files if requested
                if delete_media and media_files:
                    for media_name, media_path in media_files:
                        try:
                            if os.path.exists(media_path):
                                os.remove(media_path)
                                self.logger.info(f"Deleted {media_name.lower()}: {media_path}")
                        except Exception as e:
                            self.logger.error(f"Error deleting {media_name.lower()} {media_path}: {e}")
                
                self.refresh_themes()
            else:
                QMessageBox.warning(self, "Error", "Theme file not found.")
        except Exception as e:
            self.logger.error(f"Error deleting theme {theme_path}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete theme:\n{str(e)}")

    def get_first_theme_path(self) -> str:
        """Get the path of the first available theme (most recently modified)"""
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

    def get_startup_theme_path(self) -> str:
        """Get the theme path to load on startup based on config settings"""
        try:
            if not self.themes_dir.exists():
                return ""

            # Find all YAML files
            yaml_files = []
            for pattern in ['*.yaml', '*.yml']:
                yaml_files.extend(self.themes_dir.glob(pattern))

            if not yaml_files:
                return ""

            # Get startup mode from config
            startup_mode = self.config.get('startup_theme_mode', 'default')
            self.logger.debug(f"Startup theme mode: {startup_mode}")

            if startup_mode == 'random':
                # Pick a random theme
                selected = random.choice(yaml_files)
                self.logger.info(f"Random theme selected: {selected.name}")
                return str(selected)

            elif startup_mode == 'default':
                # Try to load the specified default theme
                default_theme = self.config.get('default_theme', '')
                if default_theme:
                    default_path = self.themes_dir / default_theme
                    if default_path.exists():
                        self.logger.info(f"Loading default theme: {default_theme}")
                        return str(default_path)
                    else:
                        self.logger.warning(f"Default theme not found: {default_theme}, falling back to last modified")
                # Fall through to last_modified behavior

            # Default: last_modified - sort by modification date
            yaml_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            self.logger.info(f"Loading last modified theme: {yaml_files[0].name}")
            return str(yaml_files[0])

        except Exception as e:
            self.logger.error(f"Error getting startup theme path: {e}")
            return ""

    def auto_load_first_theme(self):
        """Automatically load theme based on startup mode setting"""
        theme_path = self.get_startup_theme_path()
        if theme_path:
            self.theme_selected.emit(theme_path)
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
