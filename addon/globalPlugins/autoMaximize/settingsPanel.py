# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false, reportUntypedBaseClass=false, reportUnknownParameterType=false
# -*- coding: UTF-8 -*-
# AutoMaximize global plugin for NVDA
# Author: Tecwindow - https://tecwindow.net

"""GUI settings panel for AutoMaximize."""

import typing

import addonHandler
import config
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
import wx

from .consts import CONFIG_SECTION, normalizeAppName

if typing.TYPE_CHECKING:
	def _(message: str) -> str: ...

addonHandler.initTranslation()


class AutoMaximizeSettingsPanel(SettingsPanel):
	"""Settings category for AutoMaximize shown in NVDA's Settings dialog."""

	# Translators: The title of the AutoMaximize category in NVDA's Settings dialog.
	title = _("AutoMaximize")

	def makeSettings(self, settingsSizer: typing.Any) -> None:
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

		# Translators: Label for the excluded applications list in the AutoMaximize settings panel.
		excludedLabel = _("&Excluded applications:")
		rawExcluded = conf.get("excludedApplications", [])
		excludedApps = sorted({normalizeAppName(x) for x in rawExcluded if normalizeAppName(x)})
		self.excludedListBox = sHelper.addLabeledControl(
			excludedLabel,
			wx.ListBox,
			choices=excludedApps,
			style=wx.LB_SINGLE,
		)
		self.excludedListBox.Bind(wx.EVT_LISTBOX, self.onListSelect)

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: Label for the Add button in the AutoMaximize settings panel.
		self.addButton = wx.Button(self, label=_("&Add..."))
		self.addButton.Bind(wx.EVT_BUTTON, self.onAdd)
		buttonSizer.Add(self.addButton)

		# Translators: Label for the Remove button in the AutoMaximize settings panel.
		self.removeButton = wx.Button(self, label=_("&Remove"))
		self.removeButton.Bind(wx.EVT_BUTTON, self.onRemove)
		self.removeButton.Enable(False)
		buttonSizer.Add(self.removeButton)

		# Translators: Label for the Browse button in the AutoMaximize settings panel.
		self.browseButton = wx.Button(self, label=_("&Browse..."))
		self.browseButton.Bind(wx.EVT_BUTTON, self.onBrowse)
		buttonSizer.Add(self.browseButton)

		sHelper.addItem(buttonSizer)

	def onListSelect(self, event: wx.CommandEvent) -> None:
		self.removeButton.Enable(self.excludedListBox.GetSelection() != wx.NOT_FOUND)

	def onAdd(self, event: wx.CommandEvent) -> None:
		# Translators: Prompt in dialog to enter application executable name.
		prompt = _("Enter application executable name (e.g. notepad.exe):")
		# Translators: Title of dialog to enter application executable name.
		dlgTitle = _("Add Excluded Application")
		with wx.TextEntryDialog(self, prompt, dlgTitle) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				normVal = normalizeAppName(dlg.GetValue())
				if not normVal:
					return
				existing = self.excludedListBox.GetStrings()
				if normVal not in existing:
					self.excludedListBox.Append(normVal)
				self.excludedListBox.SetStringSelection(normVal)
				self.removeButton.Enable(True)
				self.excludedListBox.SetFocus()

	def onRemove(self, event: wx.CommandEvent) -> None:
		sel = self.excludedListBox.GetSelection()
		if sel == wx.NOT_FOUND:
			return
		self.excludedListBox.Delete(sel)
		count = self.excludedListBox.GetCount()
		if count > 0:
			newSel = min(sel, count - 1)
			self.excludedListBox.SetSelection(newSel)
			self.removeButton.Enable(True)
		else:
			self.removeButton.Enable(False)
		self.excludedListBox.SetFocus()

	def onBrowse(self, event: wx.CommandEvent) -> None:
		# Translators: Title of the file browser dialog to select an executable.
		message = _("Select application executable")
		# Translators: Filter string for executable files in the file browser dialog.
		wildcard = _("Executable files (*.exe)|*.exe|All files (*.*)|*.*")
		with wx.FileDialog(
			self,
			message=message,
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				normVal = normalizeAppName(dlg.GetPath())
				if not normVal:
					return
				existing = self.excludedListBox.GetStrings()
				if normVal not in existing:
					self.excludedListBox.Append(normVal)
				self.excludedListBox.SetStringSelection(normVal)
				self.removeButton.Enable(True)
				self.excludedListBox.SetFocus()

	def onSave(self) -> None:
		"""Persist the panel controls back to NVDA's configuration."""
		conf = config.conf[CONFIG_SECTION]
		conf["maximizeApplications"] = self.appsCheckBox.GetValue()
		conf["maximizeDialogs"] = self.dialogsCheckBox.GetValue()
		conf["excludedApplications"] = list(self.excludedListBox.GetStrings())
