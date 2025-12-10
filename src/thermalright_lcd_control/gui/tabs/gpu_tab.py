# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Tab widget for GPU metrics and graphs
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QCheckBox, QSpinBox, QLineEdit, QComboBox, QPushButton,
    QScrollArea, QColorDialog
)
from PySide6.QtGui import QColor


class GPUTab(QWidget):
    """Tab widget for GPU metrics configuration"""

    def __init__(self, parent, metric_widgets: dict):
        super().__init__()
        self.parent = parent
        self.metric_widgets = metric_widgets
        
        # Control widgets storage
        self.metric_checkboxes = {}
        self.metric_font_size_spins = {}
        self.metric_label_inputs = {}
        self.metric_label_position_combos = {}
        self.metric_label_font_size_spins = {}
        self.metric_unit_inputs = {}
        self.metric_freq_format_combos = {}
        
        # Bar graph controls
        self.bar_checkboxes = {}
        self.bar_metric_combos = {}
        self.bar_orientation_combos = {}
        self.bar_rotation_spins = {}
        self.bar_width_spins = {}
        self.bar_height_spins = {}
        self.bar_fill_color_btns = {}
        self.bar_bg_color_btns = {}
        self.bar_border_color_btns = {}
        self.bar_corner_radius_spins = {}
        self.bar_gradient_checkboxes = {}
        self.bar_gradient_rows = {}
        self.bar_gradient_mid_spins = {}
        self.bar_gradient_high_spins = {}
        self.bar_gradient_low_color_btns = {}
        self.bar_gradient_mid_color_btns = {}
        self.bar_gradient_high_color_btns = {}
        
        # Circular graph controls
        self.arc_checkboxes = {}
        self.arc_metric_combos = {}
        self.arc_radius_spins = {}
        self.arc_thickness_spins = {}
        self.arc_start_angle_spins = {}
        self.arc_sweep_angle_spins = {}
        self.arc_rotation_spins = {}
        self.arc_fill_color_btns = {}
        self.arc_bg_color_btns = {}
        self.arc_border_color_btns = {}
        self.arc_gradient_checkboxes = {}
        self.arc_gradient_rows = {}
        self.arc_gradient_mid_spins = {}
        self.arc_gradient_high_spins = {}
        self.arc_gradient_low_color_btns = {}
        self.arc_gradient_mid_color_btns = {}
        self.arc_gradient_high_color_btns = {}
        
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
        
        # GPU Metrics section
        metrics_group = QGroupBox("GPU Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        metrics_layout.setSpacing(6)
        metrics_layout.setContentsMargins(8, 12, 8, 8)
        
        gpu_metrics = {
            "gpu_temperature": ("Temperature:", "Temp"),
            "gpu_usage": ("Utilization:", "Usage"),
            "gpu_frequency": ("Frequency:", "Freq"),
            "gpu_mem_total": ("VRAM Total:", "VRAM"),
            "gpu_mem_percent": ("VRAM Usage:", "VRAM%"),
            "gpu_name": ("GPU Name:", "GPU"),
        }
        
        for metric_name, (row_label, display_name) in gpu_metrics.items():
            row = self._create_metric_row(row_label, display_name, metric_name)
            metrics_layout.addLayout(row)
        
        layout.addWidget(metrics_group)
        
        # GPU Bar Graphs section
        bar_group = QGroupBox("GPU Bar Graphs")
        bar_layout = QVBoxLayout(bar_group)
        bar_layout.setContentsMargins(8, 12, 8, 8)
        bar_layout.setSpacing(6)
        
        for i in range(1, 3):  # 2 GPU bar graphs
            bar_name = f"gpu_bar{i}"
            bar_row = self._create_bar_graph_row(bar_name, i)
            bar_layout.addLayout(bar_row)
            gradient_row = self._create_bar_gradient_row(bar_name)
            bar_layout.addLayout(gradient_row)
        
        layout.addWidget(bar_group)
        
        # GPU Circular Graphs section
        arc_group = QGroupBox("GPU Circular Graphs")
        arc_layout = QVBoxLayout(arc_group)
        arc_layout.setContentsMargins(8, 12, 8, 8)
        arc_layout.setSpacing(6)
        
        for i in range(1, 3):  # 2 GPU circular graphs
            arc_name = f"gpu_arc{i}"
            arc_row = self._create_circular_graph_row(arc_name, i)
            arc_layout.addLayout(arc_row)
            gradient_row = self._create_arc_gradient_row(arc_name)
            arc_layout.addLayout(gradient_row)
        
        layout.addWidget(arc_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def _create_metric_row(self, row_label, display_name, metric_name):
        """Create a single-row layout for a metric widget"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        skip_label_controls = ["gpu_name", "gpu_mem_percent"]
        
        # Row label
        label = QLabel(row_label)
        label.setFixedWidth(85)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=metric_name: self.parent.on_metric_toggled(name, checked))
        checkbox.setFixedWidth(20)
        self.metric_checkboxes[metric_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        # Size spinbox
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
            # Label input
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
            
            # Position dropdown
            pos_label = QLabel("Position:")
            pos_label.setFixedWidth(55)
            row.addWidget(pos_label, alignment=Qt.AlignVCenter)
            position_combo = QComboBox()
            position_combo.addItem("Left", "left")
            position_combo.addItem("Right", "right")
            position_combo.addItem("Above", "above")
            position_combo.addItem("Below", "below")
            position_combo.addItem("Hidden", "hidden")
            position_combo.setFixedWidth(80)
            position_combo.currentIndexChanged.connect(
                lambda idx, name=metric_name, combo=position_combo: 
                    self.parent.on_metric_label_position_changed(name, combo.currentData()))
            self.metric_label_position_combos[metric_name] = position_combo
            row.addWidget(position_combo, alignment=Qt.AlignVCenter)
            
            # Label Size spinbox
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
        
        # Frequency format for gpu_frequency
        if metric_name == "gpu_frequency":
            freq_label = QLabel("Format:")
            freq_label.setFixedWidth(50)
            row.addWidget(freq_label, alignment=Qt.AlignVCenter)
            freq_combo = QComboBox()
            freq_combo.addItem("MHz", "mhz")
            freq_combo.addItem("GHz", "ghz")
            freq_combo.setFixedWidth(70)
            freq_combo.currentIndexChanged.connect(
                lambda idx, name=metric_name, combo=freq_combo:
                    self.parent.on_metric_freq_format_changed(name, combo.currentData()))
            self.metric_freq_format_combos[metric_name] = freq_combo
            row.addWidget(freq_combo, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def _create_bar_graph_row(self, bar_name, index):
        """Create a row for bar graph controls"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        label = QLabel(f"Bar {index}:")
        label.setFixedWidth(50)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=bar_name: self.parent.on_bar_toggled(name, checked))
        self.bar_checkboxes[bar_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        metric_label = QLabel("Metric:")
        row.addWidget(metric_label, alignment=Qt.AlignVCenter)
        metric_combo = QComboBox()
        metric_combo.addItem("GPU Usage", "gpu_usage")
        metric_combo.addItem("GPU Temp", "gpu_temperature")
        metric_combo.addItem("VRAM %", "gpu_mem_percent")
        metric_combo.setFixedWidth(100)
        metric_combo.currentIndexChanged.connect(
            lambda idx, name=bar_name, combo=metric_combo:
                self.parent.on_bar_metric_changed(name, combo.currentData()))
        self.bar_metric_combos[bar_name] = metric_combo
        row.addWidget(metric_combo, alignment=Qt.AlignVCenter)
        
        orient_label = QLabel("Orient:")
        row.addWidget(orient_label, alignment=Qt.AlignVCenter)
        orient_combo = QComboBox()
        orient_combo.addItem("Horizontal", "horizontal")
        orient_combo.addItem("Vertical", "vertical")
        orient_combo.setFixedWidth(90)
        orient_combo.currentIndexChanged.connect(
            lambda idx, name=bar_name, combo=orient_combo:
                self.parent.on_bar_orientation_changed(name, combo.currentData()))
        self.bar_orientation_combos[bar_name] = orient_combo
        row.addWidget(orient_combo, alignment=Qt.AlignVCenter)
        
        # Rotation
        rot_label = QLabel("Rot:")
        row.addWidget(rot_label, alignment=Qt.AlignVCenter)
        rotation_spin = QSpinBox()
        rotation_spin.setRange(0, 359)
        rotation_spin.setValue(0)
        rotation_spin.setFixedWidth(60)
        rotation_spin.setSuffix("°")
        rotation_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_rotation_changed(name, val))
        self.bar_rotation_spins[bar_name] = rotation_spin
        row.addWidget(rotation_spin, alignment=Qt.AlignVCenter)
        
        w_label = QLabel("W:")
        row.addWidget(w_label, alignment=Qt.AlignVCenter)
        width_spin = QSpinBox()
        width_spin.setRange(10, 500)
        width_spin.setValue(100)
        width_spin.setFixedWidth(60)
        width_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_width_changed(name, val))
        self.bar_width_spins[bar_name] = width_spin
        row.addWidget(width_spin, alignment=Qt.AlignVCenter)
        
        h_label = QLabel("H:")
        row.addWidget(h_label, alignment=Qt.AlignVCenter)
        height_spin = QSpinBox()
        height_spin.setRange(5, 200)
        height_spin.setValue(20)
        height_spin.setFixedWidth(60)
        height_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_height_changed(name, val))
        self.bar_height_spins[bar_name] = height_spin
        row.addWidget(height_spin, alignment=Qt.AlignVCenter)
        
        fill_btn = QPushButton()
        fill_btn.setFixedWidth(30)
        fill_btn.setStyleSheet("background-color: #FF55FF; border: 1px solid #bdc3c7; border-radius: 4px;")
        fill_btn.setToolTip("Fill Color")
        fill_btn.clicked.connect(lambda _, name=bar_name: self._on_bar_fill_color_clicked(name))
        self.bar_fill_color_btns[bar_name] = fill_btn
        row.addWidget(fill_btn, alignment=Qt.AlignVCenter)
        
        bg_btn = QPushButton()
        bg_btn.setFixedWidth(30)
        bg_btn.setStyleSheet("background-color: #323232; border: 1px solid #bdc3c7; border-radius: 4px;")
        bg_btn.setToolTip("Background Color")
        bg_btn.clicked.connect(lambda _, name=bar_name: self._on_bar_bg_color_clicked(name))
        self.bar_bg_color_btns[bar_name] = bg_btn
        row.addWidget(bg_btn, alignment=Qt.AlignVCenter)
        
        grad_label = QLabel("Grad:")
        row.addWidget(grad_label, alignment=Qt.AlignVCenter)
        grad_checkbox = QCheckBox()
        grad_checkbox.setChecked(False)
        grad_checkbox.toggled.connect(lambda checked, name=bar_name: self._on_bar_gradient_toggled(name, checked))
        self.bar_gradient_checkboxes[bar_name] = grad_checkbox
        row.addWidget(grad_checkbox, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def _create_bar_gradient_row(self, bar_name):
        """Create gradient settings row for bar graph"""
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(55, 0, 0, 0)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)
        
        low_label = QLabel("Low:")
        container_layout.addWidget(low_label, alignment=Qt.AlignVCenter)
        low_btn = QPushButton()
        low_btn.setFixedWidth(30)
        low_btn.setStyleSheet("background-color: #00FF00; border: 1px solid #bdc3c7; border-radius: 4px;")
        low_btn.clicked.connect(lambda _, name=bar_name: self._on_bar_gradient_low_color_clicked(name))
        self.bar_gradient_low_color_btns[bar_name] = low_btn
        container_layout.addWidget(low_btn, alignment=Qt.AlignVCenter)
        
        mid_label = QLabel("Mid @")
        container_layout.addWidget(mid_label, alignment=Qt.AlignVCenter)
        mid_spin = QSpinBox()
        mid_spin.setRange(0, 100)
        mid_spin.setValue(50)
        mid_spin.setSuffix("%")
        mid_spin.setFixedWidth(65)
        mid_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_gradient_mid_changed(name, val))
        self.bar_gradient_mid_spins[bar_name] = mid_spin
        container_layout.addWidget(mid_spin, alignment=Qt.AlignVCenter)
        
        mid_btn = QPushButton()
        mid_btn.setFixedWidth(30)
        mid_btn.setStyleSheet("background-color: #FFFF00; border: 1px solid #bdc3c7; border-radius: 4px;")
        mid_btn.clicked.connect(lambda _, name=bar_name: self._on_bar_gradient_mid_color_clicked(name))
        self.bar_gradient_mid_color_btns[bar_name] = mid_btn
        container_layout.addWidget(mid_btn, alignment=Qt.AlignVCenter)
        
        high_label = QLabel("High @")
        container_layout.addWidget(high_label, alignment=Qt.AlignVCenter)
        high_spin = QSpinBox()
        high_spin.setRange(0, 100)
        high_spin.setValue(80)
        high_spin.setSuffix("%")
        high_spin.setFixedWidth(65)
        high_spin.valueChanged.connect(
            lambda val, name=bar_name: self.parent.on_bar_gradient_high_changed(name, val))
        self.bar_gradient_high_spins[bar_name] = high_spin
        container_layout.addWidget(high_spin, alignment=Qt.AlignVCenter)
        
        high_btn = QPushButton()
        high_btn.setFixedWidth(30)
        high_btn.setStyleSheet("background-color: #FF0000; border: 1px solid #bdc3c7; border-radius: 4px;")
        high_btn.clicked.connect(lambda _, name=bar_name: self._on_bar_gradient_high_color_clicked(name))
        self.bar_gradient_high_color_btns[bar_name] = high_btn
        container_layout.addWidget(high_btn, alignment=Qt.AlignVCenter)
        
        container_layout.addStretch()
        
        container.setVisible(False)
        self.bar_gradient_rows[bar_name] = container
        row.addWidget(container)
        
        return row

    def _create_circular_graph_row(self, arc_name, index):
        """Create a row for circular graph controls"""
        row = QHBoxLayout()
        row.setSpacing(6)
        
        label = QLabel(f"Arc {index}:")
        label.setFixedWidth(50)
        row.addWidget(label, alignment=Qt.AlignVCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(lambda checked, name=arc_name: self.parent.on_arc_toggled(name, checked))
        self.arc_checkboxes[arc_name] = checkbox
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)
        
        metric_label = QLabel("Metric:")
        row.addWidget(metric_label, alignment=Qt.AlignVCenter)
        metric_combo = QComboBox()
        metric_combo.addItem("GPU Usage", "gpu_usage")
        metric_combo.addItem("GPU Temp", "gpu_temperature")
        metric_combo.addItem("VRAM %", "gpu_mem_percent")
        metric_combo.setFixedWidth(100)
        metric_combo.currentIndexChanged.connect(
            lambda idx, name=arc_name, combo=metric_combo:
                self.parent.on_arc_metric_changed(name, combo.currentData()))
        self.arc_metric_combos[arc_name] = metric_combo
        row.addWidget(metric_combo, alignment=Qt.AlignVCenter)
        
        r_label = QLabel("R:")
        row.addWidget(r_label, alignment=Qt.AlignVCenter)
        radius_spin = QSpinBox()
        radius_spin.setRange(10, 200)
        radius_spin.setValue(50)
        radius_spin.setFixedWidth(60)
        radius_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_radius_changed(name, val))
        self.arc_radius_spins[arc_name] = radius_spin
        row.addWidget(radius_spin, alignment=Qt.AlignVCenter)
        
        t_label = QLabel("T:")
        row.addWidget(t_label, alignment=Qt.AlignVCenter)
        thickness_spin = QSpinBox()
        thickness_spin.setRange(2, 50)
        thickness_spin.setValue(10)
        thickness_spin.setFixedWidth(60)
        thickness_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_thickness_changed(name, val))
        self.arc_thickness_spins[arc_name] = thickness_spin
        row.addWidget(thickness_spin, alignment=Qt.AlignVCenter)
        
        start_label = QLabel("Start:")
        row.addWidget(start_label, alignment=Qt.AlignVCenter)
        start_spin = QSpinBox()
        start_spin.setRange(-360, 360)
        start_spin.setValue(135)
        start_spin.setFixedWidth(70)
        start_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_start_angle_changed(name, val))
        self.arc_start_angle_spins[arc_name] = start_spin
        row.addWidget(start_spin, alignment=Qt.AlignVCenter)
        
        sweep_label = QLabel("Sweep:")
        row.addWidget(sweep_label, alignment=Qt.AlignVCenter)
        sweep_spin = QSpinBox()
        sweep_spin.setRange(-360, 360)
        sweep_spin.setValue(270)
        sweep_spin.setFixedWidth(70)
        sweep_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_sweep_angle_changed(name, val))
        self.arc_sweep_angle_spins[arc_name] = sweep_spin
        row.addWidget(sweep_spin, alignment=Qt.AlignVCenter)
        
        # Rotation
        rot_label = QLabel("Rot:")
        row.addWidget(rot_label, alignment=Qt.AlignVCenter)
        rotation_spin = QSpinBox()
        rotation_spin.setRange(0, 359)
        rotation_spin.setValue(0)
        rotation_spin.setFixedWidth(60)
        rotation_spin.setSuffix("°")
        rotation_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_rotation_changed(name, val))
        self.arc_rotation_spins[arc_name] = rotation_spin
        row.addWidget(rotation_spin, alignment=Qt.AlignVCenter)
        
        fill_btn = QPushButton()
        fill_btn.setFixedWidth(30)
        fill_btn.setStyleSheet("background-color: #FF55FF; border: 1px solid #bdc3c7; border-radius: 4px;")
        fill_btn.setToolTip("Fill Color")
        fill_btn.clicked.connect(lambda _, name=arc_name: self._on_arc_fill_color_clicked(name))
        self.arc_fill_color_btns[arc_name] = fill_btn
        row.addWidget(fill_btn, alignment=Qt.AlignVCenter)
        
        bg_btn = QPushButton()
        bg_btn.setFixedWidth(30)
        bg_btn.setStyleSheet("background-color: #323232; border: 1px solid #bdc3c7; border-radius: 4px;")
        bg_btn.setToolTip("Background Color")
        bg_btn.clicked.connect(lambda _, name=arc_name: self._on_arc_bg_color_clicked(name))
        self.arc_bg_color_btns[arc_name] = bg_btn
        row.addWidget(bg_btn, alignment=Qt.AlignVCenter)
        
        grad_label = QLabel("Grad:")
        row.addWidget(grad_label, alignment=Qt.AlignVCenter)
        grad_checkbox = QCheckBox()
        grad_checkbox.setChecked(False)
        grad_checkbox.toggled.connect(lambda checked, name=arc_name: self._on_arc_gradient_toggled(name, checked))
        self.arc_gradient_checkboxes[arc_name] = grad_checkbox
        row.addWidget(grad_checkbox, alignment=Qt.AlignVCenter)
        
        row.addStretch()
        return row

    def _create_arc_gradient_row(self, arc_name):
        """Create gradient settings row for circular graph"""
        row = QHBoxLayout()
        row.setSpacing(6)
        row.setContentsMargins(55, 0, 0, 0)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)
        
        low_label = QLabel("Low:")
        container_layout.addWidget(low_label, alignment=Qt.AlignVCenter)
        low_btn = QPushButton()
        low_btn.setFixedWidth(30)
        low_btn.setStyleSheet("background-color: #00FF00; border: 1px solid #bdc3c7; border-radius: 4px;")
        low_btn.clicked.connect(lambda _, name=arc_name: self._on_arc_gradient_low_color_clicked(name))
        self.arc_gradient_low_color_btns[arc_name] = low_btn
        container_layout.addWidget(low_btn, alignment=Qt.AlignVCenter)
        
        mid_label = QLabel("Mid @")
        container_layout.addWidget(mid_label, alignment=Qt.AlignVCenter)
        mid_spin = QSpinBox()
        mid_spin.setRange(0, 100)
        mid_spin.setValue(50)
        mid_spin.setSuffix("%")
        mid_spin.setFixedWidth(65)
        mid_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_gradient_mid_changed(name, val))
        self.arc_gradient_mid_spins[arc_name] = mid_spin
        container_layout.addWidget(mid_spin, alignment=Qt.AlignVCenter)
        
        mid_btn = QPushButton()
        mid_btn.setFixedWidth(30)
        mid_btn.setStyleSheet("background-color: #FFFF00; border: 1px solid #bdc3c7; border-radius: 4px;")
        mid_btn.clicked.connect(lambda _, name=arc_name: self._on_arc_gradient_mid_color_clicked(name))
        self.arc_gradient_mid_color_btns[arc_name] = mid_btn
        container_layout.addWidget(mid_btn, alignment=Qt.AlignVCenter)
        
        high_label = QLabel("High @")
        container_layout.addWidget(high_label, alignment=Qt.AlignVCenter)
        high_spin = QSpinBox()
        high_spin.setRange(0, 100)
        high_spin.setValue(80)
        high_spin.setSuffix("%")
        high_spin.setFixedWidth(65)
        high_spin.valueChanged.connect(
            lambda val, name=arc_name: self.parent.on_arc_gradient_high_changed(name, val))
        self.arc_gradient_high_spins[arc_name] = high_spin
        container_layout.addWidget(high_spin, alignment=Qt.AlignVCenter)
        
        high_btn = QPushButton()
        high_btn.setFixedWidth(30)
        high_btn.setStyleSheet("background-color: #FF0000; border: 1px solid #bdc3c7; border-radius: 4px;")
        high_btn.clicked.connect(lambda _, name=arc_name: self._on_arc_gradient_high_color_clicked(name))
        self.arc_gradient_high_color_btns[arc_name] = high_btn
        container_layout.addWidget(high_btn, alignment=Qt.AlignVCenter)
        
        container_layout.addStretch()
        
        container.setVisible(False)
        self.arc_gradient_rows[arc_name] = container
        row.addWidget(container)
        
        return row

    # Color picker handlers
    def _on_bar_fill_color_clicked(self, bar_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bar_fill_color_btns[bar_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_bar_fill_color_changed(bar_name, color)

    def _on_bar_bg_color_clicked(self, bar_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bar_bg_color_btns[bar_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_bar_bg_color_changed(bar_name, color)

    def _on_bar_gradient_toggled(self, bar_name, checked):
        if bar_name in self.bar_gradient_rows:
            self.bar_gradient_rows[bar_name].setVisible(checked)
        self.parent.on_bar_gradient_toggled(bar_name, checked)

    def _on_bar_gradient_low_color_clicked(self, bar_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bar_gradient_low_color_btns[bar_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_bar_gradient_low_color_changed(bar_name, color)

    def _on_bar_gradient_mid_color_clicked(self, bar_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bar_gradient_mid_color_btns[bar_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_bar_gradient_mid_color_changed(bar_name, color)

    def _on_bar_gradient_high_color_clicked(self, bar_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bar_gradient_high_color_btns[bar_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_bar_gradient_high_color_changed(bar_name, color)

    def _on_arc_fill_color_clicked(self, arc_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.arc_fill_color_btns[arc_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_arc_fill_color_changed(arc_name, color)

    def _on_arc_bg_color_clicked(self, arc_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.arc_bg_color_btns[arc_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_arc_bg_color_changed(arc_name, color)

    def _on_arc_gradient_toggled(self, arc_name, checked):
        if arc_name in self.arc_gradient_rows:
            self.arc_gradient_rows[arc_name].setVisible(checked)
        self.parent.on_arc_gradient_toggled(arc_name, checked)

    def _on_arc_gradient_low_color_clicked(self, arc_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.arc_gradient_low_color_btns[arc_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_arc_gradient_low_color_changed(arc_name, color)

    def _on_arc_gradient_mid_color_clicked(self, arc_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.arc_gradient_mid_color_btns[arc_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_arc_gradient_mid_color_changed(arc_name, color)

    def _on_arc_gradient_high_color_clicked(self, arc_name):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.arc_gradient_high_color_btns[arc_name].setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #bdc3c7; border-radius: 4px;")
            self.parent.on_arc_gradient_high_color_changed(arc_name, color)
