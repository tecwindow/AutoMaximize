# -*- coding: UTF-8 -*-
# AutoMaximize global plugin for NVDA
# A standalone add-on to automatically maximize windows.
# Author: MesterPerfect <ahmedBakr593@gmail.com> - https://tecwindow.net

"""AutoMaximize global plugin.

Automatically maximizes the foreground window while NVDA is running.
Standard application windows and dialog windows can be controlled
independently from the NVDA Settings dialog, and the whole feature can be
toggled on or off with a configurable keyboard command that provides audible
(beep) feedback.
"""

import wx

import addonHandler
import api
import config
import core
import globalPluginHandler
import scriptHandler
import tones
import ui
import winUser
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel

addonHandler.initTranslation()

# --- Win32 constants (from winuser.h) ---------------------------------------
SC_MAXIMIZE = 0xF030          # wParam for WM_SYSCOMMAND that maximizes a window
WM_SYSCOMMAND = 0x112         # message used to send a system command to a window
WS_MAXIMIZE = 0x01000000      # window style set when a window is already maximized
WS_MAXIMIZEBOX = 0x00010000   # window style present when a window CAN be maximized

# Standard Win32 class name shared by common dialog boxes.
DIALOG_WINDOW_CLASS = "#32770"
# Window classes that must never be maximized (shell / system surfaces).
SKIP_WINDOW_CLASSES = frozenset(("Shell_TrayWnd", "DV2ControlHost"))

# How often (in milliseconds) the foreground window is inspected.
CHECK_INTERVAL = 1000

# Configuration section and specification for this add-on. Registering a spec
# lets NVDA persist the values across restarts and supplies the defaults.
CONFIG_SECTION = "autoMaximize"
CONFIG_SPEC = {
	"enabled": "boolean(default=true)",
	# Standard application windows were always maximized before, so keep that
	# behaviour by default.
	"maximizeApplications": "boolean(default=true)",
	# Dialog windows were previously skipped, so leave them opt-in by default.
	"maximizeDialogs": "boolean(default=false)",
}
config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC


class AutoMaximizeSettingsPanel(SettingsPanel):
	"""Settings category for AutoMaximize shown in NVDA's Settings dialog."""

	# Translators: The title of the AutoMaximize category in NVDA's Settings dialog.
	title = _("AutoMaximize")

	def makeSettings(self, settingsSizer):
		"""Build the panel controls and populate them from saved configuration."""
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		conf = config.conf[CONFIG_SECTION]
		# Translators: Label for a checkbox in the AutoMaximize settings panel.
		appsLabel = _("Automatically maximize standard application &windows")
		self.appsCheckBox = sHelper.addItem(wx.CheckBox(self, label=appsLabel))
		self.appsCheckBox.SetValue(conf["maximizeApplications"])
		# Translators: Label for a checkbox in the AutoMaximize settings panel.
		dialogsLabel = _("Automatically maximize &dialog windows")
		self.dialogsCheckBox = sHelper.addItem(wx.CheckBox(self, label=dialogsLabel))
		self.dialogsCheckBox.SetValue(conf["maximizeDialogs"])

	def onSave(self):
		"""Persist the panel controls back to NVDA's configuration."""
		conf = config.conf[CONFIG_SECTION]
		conf["maximizeApplications"] = self.appsCheckBox.GetValue()
		conf["maximizeDialogs"] = self.dialogsCheckBox.GetValue()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Global plugin that keeps the foreground window maximized."""

	def __init__(self):
		super().__init__()
		# Handle of the pending polling timer, or None when no check is queued.
		self._maximizeTimer = None
		# Register the settings category, guarding against a duplicate entry in
		# case the plugin is reloaded without a full NVDA restart.
		if AutoMaximizeSettingsPanel not in NVDASettingsDialog.categoryClasses:
			NVDASettingsDialog.categoryClasses.append(AutoMaximizeSettingsPanel)
		# Delay the first check so NVDA has finished initializing.
		self._scheduleCheck(CHECK_INTERVAL)

	def terminate(self):
		"""Clean up the timer and settings category on unload / reload."""
		if self._maximizeTimer is not None:
			self._maximizeTimer.Stop()
			self._maximizeTimer = None
		try:
			NVDASettingsDialog.categoryClasses.remove(AutoMaximizeSettingsPanel)
		except ValueError:
			# Not registered (e.g. already removed); nothing to do.
			pass
		super().terminate()

	def _scheduleCheck(self, delay=CHECK_INTERVAL):
		"""(Re)schedule a single foreground-window check after ``delay`` ms."""
		if self._maximizeTimer is not None:
			self._maximizeTimer.Stop()
		self._maximizeTimer = core.callLater(delay, self._onTimer)

	def _onTimer(self):
		"""Timer callback: maximize when enabled, then keep the loop alive.

		The loop keeps ticking even while the feature is disabled so that
		re-enabling it (via the toggle command) resumes maximization without
		needing an NVDA restart.
		"""
		self._maximizeTimer = None
		try:
			if config.conf[CONFIG_SECTION]["enabled"]:
				self._maximizeForegroundWindow()
		except Exception:
			# Never let an unexpected error break NVDA or stop the loop.
			pass
		finally:
			self._scheduleCheck(CHECK_INTERVAL)

	def _maximizeForegroundWindow(self):
		"""Maximize the current foreground window if configuration allows it."""
		foreground = api.getForegroundObject()
		if foreground is None:
			return
		hWnd = getattr(foreground, "windowHandle", 0)
		if hWnd:
			self._maximizeWindow(hWnd)

	def _maximizeWindow(self, hWnd):
		"""Maximize ``hWnd`` when it is eligible and enabled in configuration.

		A window is eligible only when it is not already maximized, exposes a
		maximize box, is not a shell / system surface, and has a visible title.
		Standard application windows and dialog windows are each gated by their
		own configuration option.
		"""
		windowStyle = winUser.getWindowStyle(hWnd)
		# Skip windows that are already maximized or that cannot be maximized.
		if windowStyle & WS_MAXIMIZE or not (windowStyle & WS_MAXIMIZEBOX):
			return
		className = winUser.getClassName(hWnd)
		if className in SKIP_WINDOW_CLASSES:
			return
		# Skip untitled windows (usually transient popups, menus or tooltips).
		if not winUser.getWindowText(hWnd):
			return
		conf = config.conf[CONFIG_SECTION]
		# Dialogs and standard application windows are controlled independently.
		if className == DIALOG_WINDOW_CLASS:
			if not conf["maximizeDialogs"]:
				return
		elif not conf["maximizeApplications"]:
			return
		# Ask the window to maximize itself; PostMessage keeps this asynchronous.
		winUser.PostMessage(hWnd, WM_SYSCOMMAND, SC_MAXIMIZE, 0)

	@scriptHandler.script(
		# Translators: Description of the toggle command shown in Input Gestures.
		description=_("Toggles automatic window maximization on or off"),
		# Translators: Input Gestures category for this add-on's commands.
		category=_("AutoMaximize"),
		gesture="kb:NVDA+shift+a",
	)
	def script_toggleAutoMaximize(self, gesture):
		"""Toggle the feature, giving a distinguishable beep as feedback."""
		enabled = not config.conf[CONFIG_SECTION]["enabled"]
		config.conf[CONFIG_SECTION]["enabled"] = enabled
		if enabled:
			# High-pitched beep signals that maximization is now active.
			tones.beep(880, 120)
			# Apply immediately rather than waiting for the next poll tick.
			self._scheduleCheck(0)
			# Translators: Announced when the toggle turns the feature on.
			ui.message(_("Automatic window maximization enabled"))
		else:
			# Low-pitched beep signals that maximization is now inactive.
			tones.beep(220, 120)
			# Translators: Announced when the toggle turns the feature off.
			ui.message(_("Automatic window maximization disabled"))
