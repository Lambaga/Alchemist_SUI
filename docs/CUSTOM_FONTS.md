# Custom Fonts for Menus

You can use a medieval/alchemic font for the main menus.

- Place your `.ttf`/`.otf` file in `assets/fonts/`.
- Easiest: name it `menu.ttf` (or `menu.otf`).
- Alternatively set an environment variable to a specific path:
  - Windows PowerShell: `$env:ALCHEMIST_MENU_FONT = "assets/fonts/MyMedieval.ttf"`
  - CMD: `set ALCHEMIST_MENU_FONT=assets/fonts\MyMedieval.ttf`

Notes
- When a custom font is detected, the UI automatically disables emojis in menu titles/buttons to avoid missing glyphs.
- Fallbacks remain in place; if the file is missing or invalid, the default system fonts are used.

Troubleshooting
- If the font doesn’t show, double-check the path and file extension.
- Use an absolute path in `ALCHEMIST_MENU_FONT` if relative paths fail.
- Restart the game after changing the environment variable.
