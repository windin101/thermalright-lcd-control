# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
GUI tabs package
"""

from .media_tab import MediaTab
from .themes_tab import ThemesTab
from .cpu_tab import CPUTab
from .gpu_tab import GPUTab
from .info_tab import InfoTab
from .shapes_tab import ShapesTab

__all__ = ['MediaTab', 'ThemesTab', 'CPUTab', 'GPUTab', 'InfoTab', 'ShapesTab']
