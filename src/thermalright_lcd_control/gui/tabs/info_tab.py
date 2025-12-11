# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Tab widget for Info elements (Time, Date, Custom Text, RAM)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QCheckBox, QSpinBox, QLineEdit, QComboBox, QPushButton,
    QScrollArea
)


class InfoTab(QWidget):
    """Tab widget for info elements configuration"""

    def __init__(self, parent, metric_widgets: dict):
        super().__init__()
        self.parent = parent
        self.metric_widgets = metric_widgets
        
        # Time/Date controls
        self.show_date_checkbox = None
        self.show_time_checkbox = None
        self.date_font_size_spin = None
        self.time_font_size_spin = None
        self.date_format_combo = None
        self.show_weekday_checkbox = None
        self.show_year_checkbox = None
        self.use_24_hour_checkbox = None
        self.show_seconds_checkbox = None
        self.show_am_pm_checkbox = None
        
        # RAM metrics
        self.metric_checkboxes = {}
        self.metric_font_size_spins = {}
        self.metric_label_inputs = {}
        self.metric_label_position_combos = {}
        self.metric_label_font_size_spins = {}
        self.metric_label_offset_x_spins = {}
        self.metric_label_offset_y_spins = {}
        
        # Free text controls
        self.text_checkboxes = {}
        self.text_inputs = {}
        self.text_font_size_spins = {}
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        # Time and Date section
        datetime_group = QGroupBox("Time and Date")
        datetime_layout = QVBoxLayout(datetime_group)
        datetime_layout.setContentsMargins(8, 12, 8, 8)
        datetime_layout.setSpacing(6)
        
        # Date row
        date_layout = QHBoxLayout()
        date_layout.setSpacing(6)
        
        date_layout.addWidget(QLabel("Date:"), alignment=Qt.AlignVCenter)
        self.show_date_checkbox = QCheckBox()
        self.show_date_checkbox.setChecked(True)
        self.show_date_checkbox.toggled.connect(self.parent.on_show_date_changed)
        date_layout.addWidget(self.show_date_checkbox, alignment=Qt.AlignVCenter)
        
        date_layout.addWidget(QLabel("Size:"), alignment=Qt.AlignVCenter)
        self.date_font_size_spin = QSpinBox()
        self.date_font_size_spin.setRange(8, 72)
        self.date_font_size_spin.setValue(18)
        self.date_font_size_spin.setFixedWidth(60)
        self.date_font_size_spin.valueChanged.connect(
            lambda val: self.parent.on_widget_font_size_changed('date', val))
        date_layout.addWidget(self.date_font_size_spin, alignment=Qt.AlignVCenter)
        
        date_layout.addSpacing(15)
        
        date_layout.addWidget(QLabel("Format:"), alignment=Qt.AlignVCenter)
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItem("Default", "default")
        self.date_format_combo.addItem("Short", "short")
        self.date_format_combo.addItem("Numeric", "numeric")
        self.date_format_combo.setFixedWidth(100)
        self.date_format_combo.currentIndexChanged.connect(
            lambda idx: self.parent.on_date_format_changed(self.date_format_combo.currentData()))
        date_layout.addWidget(self.date_format_combo, alignment=Qt.AlignVCenter)
        
        date_layout.addSpacing(15)
        
        date_layout.addWidget(QLabel("Weekday:"), alignment=Qt.AlignVCenter)
        self.show_weekday_checkbox = QCheckBox()
        self.show_weekday_checkbox.setChecked(True)
        self.show_weekday_checkbox.toggled.connect(self.parent.on_show_weekday_changed)
        date_layout.addWidget(self.show_weekday_checkbox, alignment=Qt.AlignVCenter)
        
        date_layout.addWidget(QLabel("Year:"), alignment=Qt.AlignVCenter)
        self.show_year_checkbox = QCheckBox()
        self.show_year_checkbox.setChecked(False)
        self.show_year_checkbox.toggled.connect(self.parent.on_show_year_changed)
        date_layout.addWidget(self.show_year_checkbox, alignment=Qt.AlignVCenter)
        
        date_layout.addStretch()
        datetime_layout.addLayout(date_layout)
        
        # Time row
        time_layout = QHBoxLayout()
        time_layout.setSpacing(6)
        
        time_layout.addWidget(QLabel("Time:"), alignment=Qt.AlignVCenter)
        self.show_time_checkbox = QCheckBox()
        self.show_time_checkbox.setChecked(False)
        self.show_time_checkbox.toggled.connect(self.parent.on_show_time_changed)
        time_layout.addWidget(self.show_time_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addWidget(QLabel("Size:"), alignment=Qt.AlignVCenter)
        self.time_font_size_spin = QSpinBox()
        self.time_font_size_spin.setRange(8, 72)
        self.time_font_size_spin.setValue(18)
        self.time_font_size_spin.setFixedWidth(60)
        self.time_font_size_spin.valueChanged.connect(
            lambda val: self.parent.on_widget_font_size_changed('time', val))
        time_layout.addWidget(self.time_font_size_spin, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        time_layout.addWidget(QLabel("24hr:"), alignment=Qt.AlignVCenter)
        self.use_24_hour_checkbox = QCheckBox()
        self.use_24_hour_checkbox.setChecked(True)
        self.use_24_hour_checkbox.toggled.connect(self.parent.on_use_24_hour_changed)
        time_layout.addWidget(self.use_24_hour_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        time_layout.addWidget(QLabel("Seconds:"), alignment=Qt.AlignVCenter)
        self.show_seconds_checkbox = QCheckBox()
        self.show_seconds_checkbox.setChecked(False)
        self.show_seconds_checkbox.toggled.connect(self.parent.on_show_seconds_changed)
        time_layout.addWidget(self.show_seconds_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addSpacing(15)
        
        time_layout.addWidget(QLabel("AM/PM:"), alignment=Qt.AlignVCenter)
        self.show_am_pm_checkbox = QCheckBox()
        self.show_am_pm_checkbox.setChecked(False)
        self.show_am_pm_checkbox.toggled.connect(self.parent.on_show_am_pm_changed)
        time_layout.addWidget(self.show_am_pm_checkbox, alignment=Qt.AlignVCenter)
        
        time_layout.addStretch()
        datetime_layout.addLayout(time_layout)
        
        layout.addWidget(datetime_group)
        
        # RAM Metrics section
        ram_group = QGroupBox("RAM Metrics")
        ram_layout = QVBoxLayout(ram_group)
        ram_layout.setSpacing(6)
        ram_layout.setContentsMargins(8, 12, 8, 8)
        
        ram_metrics = {
            "ram_total": ("RAM Total:", "Total"),
            "ram_percent": ("RAM Usage:", "Usage"),
        }
        
        for metric_name, (row_label, display_name) in ram_metrics.items():
            row = self._create_metric_row(row_label, display_name, metric_name)
            ram_layout.addLayout(row)
        
        layout.addWidget(ram_group)
        
        # Free Text section
        text_group = QGroupBox("Custom Text")
        text_layout = QVBoxLayout(text_group)
        text_layout.setContentsMargins(8, 12, 8, 8)
        text_layout.setSpacing(6)
        
        text_labels = {
            "text1": "Text 1:",
            "text2": "Text 2:",
            "text3": "Text 3:",
            "text4": "Text 4:",
        }
        
        for text_name, display_name in text_labels.items():
            text_row = self._create_text_row(text_name, display_name)
            text_layout.addLayout(text_row)
        
        layout.addWidget(text_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _create_metric_row(self, row_label, display_name, metric_name):
        """Create a single-row layout for a metric widget"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        skip_label_controls = ["ram_percent"]
        
        label = QLabel(row_label)
        label.setFixedWidth(85)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=metric_name: self.parent.on_metric_toggled(name, checked))
        checkbox.setFixedWidth(20)
        self.metric_checkboxes[metric_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        size_label = QLabel("Size:")
        size_label.setFixedWidth(35)
        row.addWidget(size_label, alignment=Qt.AlignVCenter)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(18)
        font_size_spin.setFixedWidth(60)
        font_size_spin.valueChanged.connect(
            lambda val, name=metric_name: self.parent.on_metric_font_size_changed(name, val))
        self.metric_font_size_spins[metric_name] = font_size_spin
        row.addWidget(font_size_spin, alignment=Qt.AlignVCenter)
        
        if metric_name not in skip_label_controls:
            lbl_label = QLabel("Label:")
            lbl_label.setFixedWidth(45)
            row.addWidget(lbl_label, alignment=Qt.AlignVCenter)
            label_input = QLineEdit()
            label_input.setPlaceholderText(self.metric_widgets.get(metric_name, {})._get_default_label() if metric_name in self.metric_widgets else "")
            label_input.textChanged.connect(
                lambda text, name=metric_name: self.parent.on_metric_label_changed(name, text))
            label_input.setFixedWidth(80)
            self.metric_label_inputs[metric_name] = label_input
            row.addWidget(label_input, alignment=Qt.AlignVCenter)
            
            pos_label = QLabel("Position:")
            pos_label.setFixedWidth(55)
            row.addWidget(pos_label, alignment=Qt.AlignVCenter)
            position_combo = QComboBox()
            # Grid-based positions organized by category
            position_combo.addItem("None", "none")
            position_combo.insertSeparator(position_combo.count())
            position_combo.addItem("Above Left", "above-left")
            position_combo.addItem("Above Center", "above-center")
            position_combo.addItem("Above Right", "above-right")
            position_combo.insertSeparator(position_combo.count())
            position_combo.addItem("Below Left", "below-left")
            position_combo.addItem("Below Center", "below-center")
            position_combo.addItem("Below Right", "below-right")
            position_combo.insertSeparator(position_combo.count())
            position_combo.addItem("Left Top", "left-top")
            position_combo.addItem("Left Center", "left-center")
            position_combo.addItem("Left Bottom", "left-bottom")
            position_combo.insertSeparator(position_combo.count())
            position_combo.addItem("Right Top", "right-top")
            position_combo.addItem("Right Center", "right-center")
            position_combo.addItem("Right Bottom", "right-bottom")
            position_combo.setFixedWidth(110)
            position_combo.currentIndexChanged.connect(
                lambda idx, name=metric_name, combo=position_combo: 
                    self.parent.on_metric_label_position_changed(name, combo.currentData()))
            self.metric_label_position_combos[metric_name] = position_combo
            row.addWidget(position_combo, alignment=Qt.AlignVCenter)
            
            lbl_size_label = QLabel("Lbl Size:")
            lbl_size_label.setFixedWidth(55)
            row.addWidget(lbl_size_label, alignment=Qt.AlignVCenter)
            label_font_size_spin = QSpinBox()
            label_font_size_spin.setRange(8, 72)
            label_font_size_spin.setValue(12)
            label_font_size_spin.setFixedWidth(60)
            label_font_size_spin.valueChanged.connect(
                lambda val, name=metric_name: self.parent.on_metric_label_font_size_changed(name, val))
            self.metric_label_font_size_spins[metric_name] = label_font_size_spin
            row.addWidget(label_font_size_spin, alignment=Qt.AlignVCenter)
            
            # Label offset X
            offset_x_label = QLabel("X:")
            offset_x_label.setFixedWidth(15)
            row.addWidget(offset_x_label, alignment=Qt.AlignVCenter)
            offset_x_spin = QSpinBox()
            offset_x_spin.setRange(-200, 200)
            offset_x_spin.setValue(0)
            offset_x_spin.setFixedWidth(55)
            offset_x_spin.valueChanged.connect(
                lambda val, name=metric_name: self.parent.on_metric_label_offset_x_changed(name, val))
            self.metric_label_offset_x_spins[metric_name] = offset_x_spin
            row.addWidget(offset_x_spin, alignment=Qt.AlignVCenter)
            
            # Label offset Y
            offset_y_label = QLabel("Y:")
            offset_y_label.setFixedWidth(15)
            row.addWidget(offset_y_label, alignment=Qt.AlignVCenter)
            offset_y_spin = QSpinBox()
            offset_y_spin.setRange(-200, 200)
            offset_y_spin.setValue(0)
            offset_y_spin.setFixedWidth(55)
            offset_y_spin.valueChanged.connect(
                lambda val, name=metric_name: self.parent.on_metric_label_offset_y_changed(name, val))
            self.metric_label_offset_y_spins[metric_name] = offset_y_spin
            row.addWidget(offset_y_spin, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def _create_text_row(self, text_name, display_name):
        """Create a row for free text controls"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        label = QLabel(display_name)
        label.setFixedWidth(55)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=text_name: self.parent.on_text_toggled(name, checked))
        self.text_checkboxes[text_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        text_input = QLineEdit()
        text_input.setPlaceholderText("Enter text...")
        text_input.textChanged.connect(
            lambda text, name=text_name: self.parent.on_text_changed(name, text))
        text_input.setMinimumWidth(200)
        self.text_inputs[text_name] = text_input
        row.addWidget(text_input, 1, alignment=Qt.AlignVCenter)
        
        size_label = QLabel("Size:")
        size_label.setFixedWidth(35)
        row.addWidget(size_label, alignment=Qt.AlignVCenter)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(18)
        font_size_spin.setFixedWidth(60)
        font_size_spin.valueChanged.connect(
            lambda val, name=text_name: self.parent.on_text_font_size_changed(name, val))
        self.text_font_size_spins[text_name] = font_size_spin
        row.addWidget(font_size_spin, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row
