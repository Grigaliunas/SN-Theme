# Emacs Org Mode — Standard Notes Theme

A dark theme for [Standard Notes](https://standardnotes.com/) inspired by Emacs Org Mode with Zenburn-like colors.

| Palette | Hex |
|---|---|
| Background | `#1c1c1c` |
| Editor | `#282828` |
| Foreground | `#d0d0d0` |
| Accent | `#8cd0d3` |
| Info | `#7cb8bb` |
| Success | `#6fb86f` |
| Warning | `#f0dfaf` |
| Danger | `#cc9393` |
| Link | `#93e0e3` |

## Install (Manage Plugins)

1. Open Standard Notes
2. Go to **Preferences** (bottom-left gear icon)
3. Navigate to **General** -> **Advanced Settings**
4. In the **Install External Package** field, paste:

```
https://cdn.jsdelivr.net/gh/Grigaliunas/SN-Theme@main/dist/ext.json
```

5. Press **Enter** / click **Install**
6. The theme appears in **Quick Settings** (top-left appearance icon) — select **Emacs Org Mode** to activate

## Files

```
dist/
  ext.json    — plugin descriptor (SN|Theme)
  theme.css   — StyleKit CSS variable overrides
```

## Development (local server)

Requirements: Python 3

### Generate theme files from index.html palette

```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist
```

### Generate + run local CORS server

```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist --serve --port 8001
```

Then install locally in Standard Notes — **Install External Package**:

```
http://localhost:8001/ext.json
```

### Generate standalone files for GitHub hosting

```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist \
  --cdn "https://cdn.jsdelivr.net/gh/Grigaliunas/SN-Theme@main/dist" \
  --marketing-url "https://github.com/Grigaliunas/SN-Theme"
```

### Override individual variables

```bash
python3 sn_stylekit_theme_installer.py --from-index index.html --out dist \
  --set "--sn-stylekit-info-color=#7cb8bb" \
  --set "--sn-stylekit-background-color=#1c1c1c"
```

### Use a custom variables JSON

Create `vars.json`:

```json
{
  "--sn-stylekit-background-color": "#1c1c1c",
  "--sn-stylekit-foreground-color": "#d0d0d0",
  "--sn-stylekit-border-color": "#696969"
}
```

```bash
python3 sn_stylekit_theme_installer.py --vars vars.json --out dist
```

## CLI flags

| Flag | Default | Description |
|---|---|---|
| `--from-index` | | Path to `index.html` to extract palette from |
| `--vars` | | Path to JSON file with CSS variable map |
| `--set` | | Override a CSS variable (`--set "KEY=VALUE"`, repeatable) |
| `--out` | `dist` | Output directory |
| `--name` | `Emacs Org Mode` | Theme display name |
| `--identifier` | `lt.sarunas.emacs-org-mode-theme` | Reverse-domain theme ID |
| `--version` | `1.0.0` | Semver string |
| `--description` | *(auto)* | Theme description |
| `--cdn` | | CDN base URL for standalone hosting |
| `--marketing-url` | | Link to project repo |
| `--light` | `false` | Mark as light theme |
| `--host` | `localhost` | Local server host |
| `--port` | `8001` | Local server port |
| `--serve` | `false` | Run local CORS server after generating |
| `--no-optional-overrides` | `false` | Skip optional override variables |

## License

MIT
