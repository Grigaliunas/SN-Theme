# Standard Notes StyleKit Theme – Python installer (SN|Theme)

This folder contains a Python script that:
- generates `theme.css` (StyleKit CSS variable overrides)
- generates `ext.json` (Standard Notes plugin descriptor for themes)
- optionally runs a local HTTP server with CORS enabled

## Requirements
- Python 3
- Standard Notes desktop/web app (for importing `ext.json`)

## Files
- `sn_stylekit_theme_installer.py` – generator + local CORS server

## Generate from `index.html` (palette + font)
```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist
```

Output:
- `dist/theme.css`
- `dist/ext.json`

## Generate + run local server (CORS enabled)
```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist --serve --port 8001
```

When running, URLs are:
- `http://localhost:8001/ext.json`
- `http://localhost:8001/theme.css`

## Import into Standard Notes
Standard Notes → **Extensions** → **Import Extension** → paste:
- `http://localhost:8001/ext.json`

## Override a variable
Example:
```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist \
  --set "--sn-stylekit-info-color=#7cb8bb" \
  --set "--sn-stylekit-background-color=#1c1c1c"
```

## Use a custom variables JSON
Create `vars.json` like:
```json
{
  "--sn-stylekit-background-color": "#1c1c1c",
  "--sn-stylekit-foreground-color": "#d0d0d0",
  "--sn-stylekit-border-color": "#696969"
}
```

Run:
```bash
python3 sn_stylekit_theme_installer.py --vars vars.json --out dist --serve
```
