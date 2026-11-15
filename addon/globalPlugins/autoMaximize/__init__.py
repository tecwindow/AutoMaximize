# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false
# -*- coding: UTF-8 -*-
# AutoMaximize global plugin for NVDA
# A standalone add-on to automatically maximize windows.
# Author: Tecwindow - https://tecwindow.net

"""AutoMaximize global plugin.

Automatically maximizes eligible application windows while NVDA is running.
Standard application windows and dialog windows can be controlled
independently from the NVDA Settings dialog, and the whole feature can be
toggled on or off with a configurable keyboard command that provides audible
(beep) feedback.
Specific applications can be excluded from automatic maximization.
"""

import typing

import addonHandler
import api
import appModuleHandler
import config
import core
import globalPluginHandler
import logHandler
import scriptHandler
import tones
import ui
import winUser
from gui.settingsDialogs import NVDASettingsDialog

from .consts import (
	CHECK_INTERVAL,
	CONFIG_SECTION,
	CONFIG_SPEC,
	DIALOG_WINDOW_CLASS,
	SC_MAXIMIZE,
	SKIP_WINDOW_CLASSES,
	WM_SYSCOMMAND,
	WS_MAXIMIZE,
	WS_MAXIMIZEBOX,
	normalizeAppName,
)
from .settingsPanel import AutoMaximizeSettingsPanel

# Provide a stub for the gettext translation function so type checkers recognize it.
if typing.TYPE_CHECKING:
	def _(message: str) -> str: ...

addonHandler.initTranslation()

# Register the configuration specification with NVDA.
config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Global plugin that keeps the foreground window maximized."""

	def __init__(self) -> None:
		super().__init__()
		self._maximizeTimer: typing.Any = None
		# Register the settings category, guarding against a duplicate entry in
		# case the plugin is reloaded without a full NVDA restart.
		if AutoMaximizeSettingsPanel not in NVDASettingsDialog.categoryClasses:
			NVDASettingsDialog.categoryClasses.append(AutoMaximizeSettingsPanel)
		self._scheduleCheck(CHECK_INTERVAL)

	def terminate(self) -> None:
		"""Clean up the timer and settings category on unload / reload."""
		if self._maximizeTimer is not None:
			self._maximizeTimer.Stop()
			self._maximizeTimer = None
		try:
			NVDASettingsDialog.categoryClasses.remove(AutoMaximizeSettingsPanel)
		except ValueError:
			pass
		super().terminate()

	def _scheduleCheck(self, delay: int = CHECK_INTERVAL) -> None:
		"""(Re)schedule a single foreground-window check after ``delay`` ms."""
		if self._maximizeTimer is not None:
			self._maximizeTimer.Stop()
		self._maximizeTimer = core.callLater(delay, self._onTimer)

	def _onTimer(self) -> None:
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
			logHandler.log.exception("AutoMaximize timer failed")
		finally:
			self._scheduleCheck(CHECK_INTERVAL)

	def _getAppNameFromHWnd(self, hWnd: int) -> str | None:
		"""Get the process executable name for a given window handle."""
		try:
			processID = winUser.getWindowThreadProcessID(hWnd)[0]
			if processID:
				appName = appModuleHandler.getAppNameFromProcessID(processID, False)
				if appName:
					return appName
		except Exception:  # noqa: BLE001
			pass
		return None

	def _maximizeForegroundWindow(self) -> None:
		"""Maximize the current foreground window if configuration allows it."""
		foreground = api.getForegroundObject()
		if foreground is None:
			return
		hWnd = getattr(foreground, "windowHandle", 0)
		if hWnd:
			self._maximizeWindow(hWnd)

	def _maximizeWindow(self, hWnd: int) -> None:
		"""Maximize ``hWnd`` when it is eligible and enabled in configuration.

		A window is eligible only when it is not already maximized, exposes a
		maximize box, is not a shell / system surface, has a visible title,
		and is not present in the excluded applications list.
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

		# Check if the application is in the exclusion list.
		appName = self._getAppNameFromHWnd(hWnd)
		if appName:
			normName = normalizeAppName(appName)
			conf = config.conf[CONFIG_SECTION]
			excluded = {normalizeAppName(x) for x in conf.get("excludedApplications", [])}
			if normName in excluded:
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
	def script_toggleAutoMaximize(self, gesture: typing.Any) -> None:
		"""Toggle the feature, giving a distinguishable beep as feedback."""
		enabled = not config.conf[CONFIG_SECTION]["enabled"]
		config.conf[CONFIG_SECTION]["enabled"] = enabled
		if enabled:
			# High-pitched beep signals that maximization is now active.
			tones.beep(880, 120)
			self._scheduleCheck(0)
			# Translators: Announced when the toggle turns the feature on.
			ui.message(_("Automatic window maximization enabled"))
		else:
			# Low-pitched beep signals that maximization is now inactive.
			tones.beep(220, 120)
			# Translators: Announced when the toggle turns the feature off.
			ui.message(_("Automatic window maximization disabled"))

	@scriptHandler.script(
		# Translators: Description of the command to add or remove current app from the auto-maximize list.
		description=_("Adds or removes the current application from the auto-maximize list"),
		# Translators: Input Gestures category for this add-on's commands.
		category=_("AutoMaximize"),
	)
	def script_toggleCurrentAppExclusion(self, gesture: typing.Any) -> None:
		"""Toggle the active application into or out of the excluded list."""
		foreground = api.getForegroundObject()
		appName = None
		if foreground is not None:
			hWnd = getattr(foreground, "windowHandle", 0)
			if hWnd:
				appName = self._getAppNameFromHWnd(hWnd)
			if not appName:
				try:
					appName = foreground.appModule.appName
				except Exception:  # noqa: BLE001
					appName = None

		if not appName:
			# Translators: Announced when the current application name could not be identified.
			ui.message(_("Could not determine current application name"))
			return

		normName = normalizeAppName(appName)
		conf = config.conf[CONFIG_SECTION]
		rawExcluded = conf.get("excludedApplications", [])
		excluded = [normalizeAppName(x) for x in rawExcluded if normalizeAppName(x)]

		if normName in excluded:
			excluded = [x for x in excluded if x != normName]
			conf["excludedApplications"] = excluded
			tones.beep(220, 100)
			# Translators: Announced when an application is removed from the excluded list.
			ui.message(_("{app} removed from excluded applications").format(app=normName))
			if conf.get("enabled", True):
				self._scheduleCheck(0)
		else:
			excluded.append(normName)
			conf["excludedApplications"] = excluded
			tones.beep(880, 100)
			# Translators: Announced when an application is added to the excluded list.
			ui.message(_("{app} added to excluded applications").format(app=normName))
