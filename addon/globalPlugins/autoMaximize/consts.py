# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false
# -*- coding: UTF-8 -*-
# AutoMaximize global plugin for NVDA
# Author: Tecwindow - https://tecwindow.net

"""Constants, configuration specification, and helper utilities for AutoMaximize."""

import os

# --- Win32 constants (from winuser.h) ---------------------------------------
SC_MAXIMIZE: int = 0xF030          # wParam for WM_SYSCOMMAND that maximizes a window
WM_SYSCOMMAND: int = 0x112         # message used to send a system command to a window
WS_MAXIMIZE: int = 0x01000000      # window style set when a window is already maximized
WS_MAXIMIZEBOX: int = 0x00010000   # window style present when a window CAN be maximized

# Standard Win32 class name shared by common dialog boxes.
DIALOG_WINDOW_CLASS: str = "#32770"
# Window classes that must never be maximized (shell / system surfaces).
SKIP_WINDOW_CLASSES: frozenset[str] = frozenset(("Shell_TrayWnd", "DV2ControlHost"))

# How often (in milliseconds) the foreground window is inspected.
CHECK_INTERVAL: int = 1000

# Configuration section and specification for this add-on.
CONFIG_SECTION: str = "autoMaximize"
CONFIG_SPEC: dict[str, str] = {
	"enabled": "boolean(default=true)",
	# Standard application windows were always maximized before, so keep that
	# behaviour by default.
	"maximizeApplications": "boolean(default=true)",
	# Dialog windows were previously skipped, so leave them opt-in by default.
	"maximizeDialogs": "boolean(default=false)",
	# List of executable names excluded from auto-maximization.
	"excludedApplications": "string_list(default=list())",
}


def normalizeAppName(name: str) -> str:
	"""Normalize application executable name to lowercase base filename.

	Removes path components if present and ensures a '.exe' extension.
	"""
	name = os.path.basename(name).strip().lower()
	if name and not name.endswith(".exe"):
		name = f"{name}.exe"
	return name
