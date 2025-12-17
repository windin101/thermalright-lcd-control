"""
Path Resolution Utilities
Handles dynamic path resolution for different installation environments.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from thermalright_lcd_control.common.logging_config import get_gui_logger


class PathResolver:
    """Resolves paths for different installation environments"""

    def __init__(self):
        self.logger = get_gui_logger()
        self._installation_root = None
        self._resources_root = None

    def get_installation_root(self) -> Path:
        """Get the root directory where the application is installed"""
        if self._installation_root is not None:
            return self._installation_root

        # Try different installation locations in order of preference
        possible_roots = [
            # System-wide installation
            Path("/usr/share/thermalright-lcd-control"),
            Path("/usr/local/share/thermalright-lcd-control"),
            # User installation
            Path.home() / ".local" / "share" / "thermalright-lcd-control",
            # Development environment (current directory)
            Path.cwd(),
        ]

        for root in possible_roots:
            if self._is_valid_installation(root):
                self._installation_root = root
                self.logger.info(f"Detected installation root: {root}")
                return root

        # Fallback to current directory
        self._installation_root = Path.cwd()
        self.logger.warning(f"No valid installation found, using current directory: {self._installation_root}")
        return self._installation_root

    def get_resources_root(self) -> Path:
        """Get the resources directory"""
        if self._resources_root is not None:
            return self._resources_root

        installation_root = self.get_installation_root()

        # Check for resources in different locations
        possible_resources = [
            installation_root / "resources",
            installation_root / "src" / "thermalright_lcd_control" / "resources",  # Development
        ]

        for resources in possible_resources:
            if resources.exists() and resources.is_dir():
                self._resources_root = resources
                self.logger.info(f"Detected resources root: {resources}")
                return resources

        # Fallback
        self._resources_root = installation_root / "resources"
        self.logger.warning(f"No resources directory found, using: {self._resources_root}")
        return self._resources_root

    def _is_valid_installation(self, path: Path) -> bool:
        """Check if the path contains a valid installation"""
        if not path.exists() or not path.is_dir():
            return False

        # Check for key files/directories that indicate a valid installation
        indicators = [
            path / "resources",
            path / "thermalright_lcd_control",
            path / "pyproject.toml",
        ]

        return any(indicator.exists() for indicator in indicators)

    def resolve_background_path(self, theme_path: str) -> str:
        """Convert theme background path to actual filesystem path"""
        if not theme_path:
            return theme_path

        # Handle hardcoded installation paths
        if theme_path.startswith("/usr/share/thermalright-lcd-control/"):
            # Replace with actual installation path
            resources_root = self.get_resources_root()
            relative_path = theme_path.replace("/usr/share/thermalright-lcd-control/", "")
            
            # Try themes subdirectory first
            themes_path = resources_root / "themes" / relative_path
            if themes_path.exists():
                self.logger.debug(f"Resolved background path to themes: {theme_path} -> {themes_path}")
                return str(themes_path)
            
            # Try direct resources path
            resolved_path = resources_root / relative_path
            if resolved_path.exists():
                self.logger.debug(f"Resolved background path: {theme_path} -> {resolved_path}")
                return str(resolved_path)
            
            # Fallback to original path if it exists
            if Path(theme_path).exists():
                self.logger.debug(f"Using original path (exists): {theme_path}")
                return theme_path

        # If it's already an absolute path and exists, return as-is
        if Path(theme_path).is_absolute() and Path(theme_path).exists():
            return theme_path

        # Handle relative paths
        if not Path(theme_path).is_absolute():
            resources_root = self.get_resources_root()
            relative_path = theme_path.lstrip("./")
            if relative_path.startswith("resources/"):
                relative_path = relative_path[len("resources/"):]
            resolved_path = resources_root / relative_path
            if resolved_path.exists():
                return str(resolved_path)

        # Return original path if no resolution worked
        self.logger.debug(f"Could not resolve background path: {theme_path}")
        return theme_path

    def resolve_foreground_path(self, theme_path: str, resolution: str) -> str:
        """Convert theme foreground path to actual filesystem path"""
        if not theme_path:
            return theme_path

        # Format the path with resolution
        formatted_path = theme_path.format(resolution=resolution)

        # Use same resolution logic as background
        return self.resolve_background_path(formatted_path)


# Global instance
_path_resolver = None

def get_path_resolver() -> PathResolver:
    """Get the global path resolver instance"""
    global _path_resolver
    if _path_resolver is None:
        _path_resolver = PathResolver()
    return _path_resolver
