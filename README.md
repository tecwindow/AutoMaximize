# AutoMaximize - Maximize every window automatically

* Author: TecWindow
* Website: [https://tecwindow.net](https://tecwindow.net)
* [Telegram channel][https://t.me/tecwindow](https://t.me/tecwindow)
* donation link: [https://paypal.me/Qais1461](https://paypal.me/Qais1461)

AutoMaximize automatically maximizes application windows while NVDA is running, so you do not need to manually use the maximize button every time you open or switch to a window.

The main purpose of the add-on is to keep application windows maximized, helping ensure that buttons, controls, and other interface elements remain visible and accessible. In some applications, especially web-based applications, certain controls or interface elements may be hidden or rearranged when the window is not maximized.

AutoMaximize can also be useful for users who create video tutorials or screen recordings and want application windows and their interface elements to remain clearly visible while demonstrating programs.

The add-on runs a low-overhead background check and provides independent control over the maximization of standard application windows and dialog windows.

## Shortcuts

* NVDA+Shift+A: turns automatic window maximization on or off. A high-pitched beep indicates that maximization has been enabled, while a low-pitched beep indicates that it has been disabled.

You can change or remove this shortcut via the Input Gestures dialog, under the AutoMaximize category.

## Settings

AutoMaximize provides a dedicated category in NVDA's Settings dialog.

The following options are available:

* Automatically maximize standard application windows: maximizes regular application windows. This option is enabled by default.
* Automatically maximize dialog windows: maximizes resizable dialog windows that provide a maximize button. This option is disabled by default.

Settings are saved automatically and restored when NVDA starts.

## Usage notes

AutoMaximize starts working automatically after installation. Also note the following:

* A window is only maximized if it can actually be maximized and is not already maximized.
* Standard application windows and dialog windows can be controlled independently.
* System surfaces such as the taskbar are never maximized.
* Untitled or transient windows, such as menus and tooltips, are not maximized.
* The add-on can be temporarily disabled and enabled using its assigned command.
* All text displayed by the add-on is translatable.
* The add-on currently includes English and Arabic translations.

## Support

For source code, bug reports, or contributions, visit the [AutoMaximize project on GitHub][https://github.com/tecwindow/AutoMaximize].

For more software, accessibility tools, and technology content, visit the [TecWindow website][https://tecwindow.net].

## Changes

### Version 1.1

* Added a dedicated AutoMaximize category to NVDA's Settings dialog with independent options for standard application windows and dialog windows.
* Settings are now saved and restored across NVDA restarts.
* Added a toggle command, NVDA+Shift+A by default, to enable or disable automatic window maximization.
* Added a high-pitched beep when maximization is enabled and a low-pitched beep when it is disabled.
* Standard application windows and dialog windows can now be controlled independently.
* All user-facing text is now translatable.
* Added English and Arabic translations.
* Updated the add-on for NVDA 2026 compatibility and modern add-on APIs.
* Raised the minimum supported NVDA version to 2024.1.
* Improved the reliability of the background check and added safe cleanup when the add-on is reloaded or unloaded.

### Version 1.0

* Initial release.
* Automatically maximizes the foreground window.
