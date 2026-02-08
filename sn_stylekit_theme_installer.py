#!/usr/bin/env python3
"""
Standard Notes StyleKit theme installer (SN|Theme)

What it does:
- Generates theme.css that overrides Standard Notes StyleKit CSS variables.
- Generates ext.json for importing the theme as a Standard Notes plugin.
- Optional: runs a local HTTP server with CORS headers for Standard Notes import.

Docs references:
- "Building a theme plugin" (StyleKit variables) and "Running a plugin locally" (CORS + ext.json + themes area).

Usage examples:

  # 1) Generate files (dist/theme.css + dist/ext.json) from an index.html palette
  python3 sn_stylekit_theme_installer.py --from-index index.html --out dist

  # 2) Generate + run local server (CORS enabled)
  python3 sn_stylekit_theme_installer.py --from-index index.html --out dist --serve --port 8001

  # 3) Generate from custom vars JSON
  python3 sn_stylekit_theme_installer.py --vars vars.json --out dist --serve

  # 4) Override one variable
  python3 sn_stylekit_theme_installer.py --from-index index.html --set "--sn-stylekit-info-color=#7cb8bb" --out dist

  # 5) Generate standalone files for GitHub hosting (no local server needed)
  python3 sn_stylekit_theme_installer.py --from-index index.html --out dist \
    --cdn "https://cdn.jsdelivr.net/gh/Grigaliunas/SN-Theme@latest/dist" \
    --marketing-url "https://github.com/Grigaliunas/SN-Theme"

Then in Standard Notes:
- Local:  Preferences → General → Advanced → Install External Package → http://localhost:8001/ext.json
- Hosted: Preferences → General → Advanced → Install External Package →
          https://cdn.jsdelivr.net/gh/Grigaliunas/SN-Theme@latest/dist/ext.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Iterable, Tuple


HEX6_RE = re.compile(r"#[0-9a-fA-F]{6}")


@dataclass(frozen=True)
class ThemeMeta:
    identifier: str
    name: str
    version: str
    host: str
    port: int
    description: str = ""
    is_dark: bool = True
    cdn_base: str = ""
    marketing_url: str = ""
    dock_icon: Dict | None = None
    css_filename: str = "theme.css"
    ext_filename: str = "ext.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_font_family_from_index(html: str) -> str:
    """
    Extracts the first 'font-family: ...;' match from the HTML/CSS.
    Fallback: "'Courier New', monospace"
    """
    m = re.search(r"font-family:\s*([^;]+);", html, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "'Courier New', monospace")


def extract_hex_colors_from_index(html: str) -> Tuple[str, ...]:
    """
    Returns sorted unique #RRGGBB colors found in the HTML.
    """
    colors = sorted(set(HEX6_RE.findall(html)), key=lambda s: s.lower())
    return tuple(colors)


def palette_from_index(index_path: Path) -> Dict[str, str]:
    """
    Maps palette slots to colors found in index.html.
    Uses defaults if not present.
    """
    html = _read_text(index_path)
    colors = {c.lower() for c in extract_hex_colors_from_index(html)}

    def pick(wanted: str, default: str) -> str:
        return wanted if wanted.lower() in colors else default

    return {
        "font_family": extract_font_family_from_index(html),
        "background": pick("#1c1c1c", "#1c1c1c"),
        "editor_background": pick("#282828", "#282828"),
        "panel_background": pick("#2a2a2a", "#2a2a2a"),
        "selection_background": pick("#2f2f2f", "#2f2f2f"),
        "status_background": pick("#343434", "#343434"),
        "header_background": pick("#383838", "#383838"),
        "dim_border": pick("#505050", "#505050"),
        "border": pick("#696969", "#696969"),
        "success": pick("#6fb86f", "#2b9612"),
        "info": pick("#7cb8bb", "#086dd6"),
        "comment": pick("#7f9f7f", "#989898"),
        "accent": pick("#8cd0d3", "#7049cf"),
        "link": pick("#93e0e3", "#086dd6"),
        "muted": pick("#c0c0c0", "#989898"),
        "danger": pick("#cc9393", "#f80324"),
        "foreground": pick("#d0d0d0", "#d0d0d0"),
        "light_foreground": pick("#dcdccc", "#ffffff"),
        "warning": pick("#f0dfaf", "#f6a200"),
    }


def stylekit_vars_from_palette(p: Dict[str, str]) -> Dict[str, str]:
    """
    Produces a StyleKit variable map from palette slots.
    Variable names follow Standard Notes docs.
    """
    bg = p["background"]
    fg = p["foreground"]

    return {
        # Font
        "--sn-stylekit-monospace-font": p["font_family"],
        "--sn-stylekit-sans-serif-font": p["font_family"],

        # Core colors
        "--sn-stylekit-background-color": bg,
        "--sn-stylekit-foreground-color": fg,
        "--sn-stylekit-border-color": p["border"],

        "--sn-stylekit-contrast-background-color": p["editor_background"],
        "--sn-stylekit-contrast-foreground-color": p["muted"],
        "--sn-stylekit-contrast-border-color": p["border"],

        "--sn-stylekit-secondary-background-color": p["panel_background"],
        "--sn-stylekit-secondary-foreground-color": fg,
        "--sn-stylekit-secondary-border-color": p["border"],

        "--sn-stylekit-secondary-contrast-background-color": p["header_background"],
        "--sn-stylekit-secondary-contrast-foreground-color": fg,
        # Docs page contains a typo for secondary-contrast-border. Use the expected name:
        "--sn-stylekit-secondary-contrast-border-color": p["border"],

        # Editor
        "--sn-stylekit-editor-background-color": p["editor_background"],
        "--sn-stylekit-editor-foreground-color": fg,

        # Semantic colors
        "--sn-stylekit-neutral-color": p["muted"],
        "--sn-stylekit-neutral-contrast-color": bg,

        "--sn-stylekit-info-color": p["info"],
        "--sn-stylekit-info-contrast-color": bg,

        "--sn-stylekit-success-color": p["success"],
        "--sn-stylekit-success-contrast-color": bg,

        "--sn-stylekit-warning-color": p["warning"],
        "--sn-stylekit-warning-contrast-color": bg,

        "--sn-stylekit-danger-color": p["danger"],
        "--sn-stylekit-danger-contrast-color": bg,

        # Misc UI tokens
        "--sn-stylekit-shadow-color": p["dim_border"],
        "--sn-stylekit-paragraph-text-color": fg,
        "--sn-stylekit-input-placeholder-color": p["comment"],
        "--sn-stylekit-input-border-color": p["border"],
        "--sn-stylekit-scrollbar-thumb-color": p["dim_border"],
        "--sn-stylekit-scrollbar-track-border-color": p["border"],
        "--sn-stylekit-general-border-radius": "2px",

        # Greyscale ramp (optional)
        "--sn-stylekit-grey-1": p["dim_border"],
        "--sn-stylekit-grey-2": p["border"],
        "--sn-stylekit-grey-3": p["selection_background"],
        "--sn-stylekit-grey-4": p["status_background"],
        "--sn-stylekit-grey-4-opacity-variant": p["status_background"] + "80",  # 50% alpha
        "--sn-stylekit-grey-5": p["header_background"],
        "--sn-stylekit-grey-6": p["editor_background"],

        # Accessory tints (optional)
        "--sn-stylekit-accessory-tint-color-1": p["info"],
        "--sn-stylekit-accessory-tint-color-2": p["danger"],
        "--sn-stylekit-accessory-tint-color-3": p["warning"],
        "--sn-stylekit-accessory-tint-color-4": p["accent"],
        "--sn-stylekit-accessory-tint-color-5": p["success"],
        "--sn-stylekit-accessory-tint-color-6": p["link"],
    }


def optional_overrides_from_palette(p: Dict[str, str]) -> Dict[str, str]:
    """
    Optional override variables listed in Standard Notes theme docs.
    """
    return {
        "--modal-background-color": "var(--sn-stylekit-background-color)",
        "--editor-header-bar-background-color": p["header_background"],
        "--editor-background-color": "var(--sn-stylekit-editor-background-color)",
        "--editor-foreground-color": "var(--sn-stylekit-editor-foreground-color)",
        "--editor-title-bar-border-bottom-color": "var(--sn-stylekit-border-color)",
        "--editor-title-input-color": "var(--sn-stylekit-editor-foreground-color)",

        "--editor-pane-background-color": "var(--sn-stylekit-background-color)",
        "--editor-pane-editor-background-color": "var(--sn-stylekit-editor-background-color)",
        "--editor-pane-editor-foreground-color": "var(--sn-stylekit-editor-foreground-color)",
        "--editor-pane-component-stack-item-background-color": "var(--sn-stylekit-background-color)",

        "--text-selection-color": "var(--sn-stylekit-info-contrast-color)",
        "--text-selection-background-color": "var(--sn-stylekit-info-color)",

        "--items-column-background-color": "var(--sn-stylekit-background-color)",
        "--items-column-items-background-color": "var(--sn-stylekit-background-color)",
        "--items-column-border-left-color": "var(--sn-stylekit-border-color)",
        "--items-column-border-right-color": "var(--sn-stylekit-border-color)",

        "--items-column-search-background-color": "var(--sn-stylekit-contrast-background-color)",
        "--item-cell-selected-background-color": "var(--sn-stylekit-contrast-background-color)",
        "--item-cell-selected-border-left-color": "var(--sn-stylekit-info-color)",

        "--navigation-column-background-color": "var(--sn-stylekit-secondary-background-color)",
        "--navigation-section-title-color": "var(--sn-stylekit-secondary-foreground-color)",
        "--navigation-item-text-color": "var(--sn-stylekit-secondary-foreground-color)",
        "--navigation-item-count-color": "var(--sn-stylekit-neutral-color)",

        "--panel-resizer-background-color": "var(--sn-stylekit-secondary-contrast-background-color)",
        "--link-element-color": p["link"],
    }


def build_theme_css(vars_map: Dict[str, str], extra_css: str = "") -> str:
    """
    Returns theme.css content.
    """
    lines = [":root {"]
    for k in sorted(vars_map.keys(), key=str.lower):
        v = vars_map[k]
        # If font family contains commas/spaces, keep as-is. Values are used verbatim.
        lines.append(f"  {k}: {v};")
    lines.append("}")
    if extra_css.strip():
        lines.append("")
        lines.append(extra_css.rstrip() + "\n")
    return "\n".join(lines) + "\n"


def build_ext_json(meta: ThemeMeta) -> Dict[str, str]:
    """
    ext.json for SN|Theme.
    The 'url' should point directly to theme.css for themes.
    When cdn_base is set, URLs point to the public CDN instead of localhost.
    """
    if meta.cdn_base:
        base = meta.cdn_base.rstrip("/")
        css_url = f"{base}/{meta.css_filename}"
        ext_url = f"{base}/{meta.ext_filename}"
    else:
        css_url = f"http://{meta.host}:{meta.port}/{meta.css_filename}"
        ext_url = None

    result: Dict[str, str] = {
        "identifier": meta.identifier,
        "name": meta.name,
        "content_type": "SN|Theme",
        "area": "themes",
        "version": meta.version,
        "description": meta.description,
        "url": css_url,
        "isDark": meta.is_dark,
    }
    if ext_url:
        result["latest_url"] = ext_url
    if meta.marketing_url:
        result["marketing_url"] = meta.marketing_url
    if meta.dock_icon:
        result["dock_icon"] = meta.dock_icon
    return result


def parse_set_overrides(items: Iterable[str]) -> Dict[str, str]:
    """
    Parse repeated --set "KEY=VALUE" pairs.
    KEY should be a CSS variable name like --sn-stylekit-background-color
    """
    out: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"--set expects KEY=VALUE, got: {item}")
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"Empty KEY in --set: {item}")
        out[k] = v
    return out


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """
    Simple static server with CORS headers.
    Standard Notes local setup docs require CORS to load extensions.
    """
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.end_headers()


def serve_directory(directory: Path, host: str, port: int) -> None:
    """
    Serve a directory with CORS enabled.
    """
    import os

    os.chdir(directory)
    httpd = ThreadingHTTPServer((host, port), CORSRequestHandler)
    print(f"[server] Serving {directory} at http://{host}:{port}/ (CORS: *)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sn_stylekit_theme_installer.py",
        description="Generate and optionally serve a Standard Notes SN|Theme from StyleKit CSS variables.",
    )
    ap.add_argument("--from-index", type=str, default="", help="Path to index.html to extract palette from.")
    ap.add_argument("--vars", type=str, default="", help="Path to JSON file containing CSS variable map.")
    ap.add_argument("--set", dest="set_overrides", action="append", default=[],
                    help='Override/add a CSS variable. Format: --set "--sn-stylekit-info-color=#7cb8bb" (repeatable)')
    ap.add_argument("--out", type=str, default="dist", help="Output directory for ext.json and theme.css.")
    ap.add_argument("--name", type=str, default="Emacs Org Mode", help="Theme name in Standard Notes.")
    ap.add_argument("--identifier", type=str, default="lt.sarunas.emacs-org-mode-theme", help="Theme identifier.")
    ap.add_argument("--version", type=str, default="1.0.0", help="Theme version string.")
    ap.add_argument("--host", type=str, default="localhost", help="Host for local server and URL in ext.json.")
    ap.add_argument("--port", type=int, default=8001, help="Port for local server and URL in ext.json.")
    ap.add_argument("--no-optional-overrides", action="store_true", help="Do not emit optional override variables.")
    ap.add_argument("--description", type=str, default="A dark theme inspired by Emacs Org Mode with Zenburn-like colors",
                    help="Theme description shown in Standard Notes.")
    ap.add_argument("--light", action="store_true", help="Mark theme as light (default is dark).")
    ap.add_argument("--cdn", type=str, default="",
                    help="CDN base URL for standalone hosting (e.g. https://cdn.jsdelivr.net/gh/USER/REPO@TAG/dist). "
                         "When set, ext.json URLs point here instead of localhost.")
    ap.add_argument("--marketing-url", type=str, default="", help="URL to project homepage / GitHub repo.")
    ap.add_argument("--serve", action="store_true", help="Run a local CORS-enabled server after generating files.")
    args = ap.parse_args(list(argv) if argv is not None else None)

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    vars_map: Dict[str, str] = {}

    if args.vars:
        vars_path = Path(args.vars)
        if not vars_path.exists():
            print(f"[error] vars file not found: {vars_path}", file=sys.stderr)
            return 2
        vars_map.update(json.loads(_read_text(vars_path)))

    if args.from_index:
        index_path = Path(args.from_index)
        if not index_path.exists():
            print(f"[error] index.html not found: {index_path}", file=sys.stderr)
            return 2
        pal = palette_from_index(index_path)
        vars_map.update(stylekit_vars_from_palette(pal))
        if not args.no_optional_overrides:
            vars_map.update(optional_overrides_from_palette(pal))

        # Set link color also on anchors (non-variable) to keep preview consistent in some contexts.
        extra_css = f"a {{ color: {pal['link']}; }}\n"
    else:
        extra_css = ""

    # Apply --set overrides last
    try:
        vars_map.update(parse_set_overrides(args.set_overrides))
    except ValueError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2

    if not vars_map:
        print("[error] No variables generated. Use --from-index or --vars.", file=sys.stderr)
        return 2

    # Build dock icon from palette if available
    dock_icon = None
    if args.from_index:
        dock_icon = {
            "type": "circle",
            "background_color": pal["background"],
            "foreground_color": pal["accent"],
            "border_color": pal["info"],
        }

    meta = ThemeMeta(
        identifier=args.identifier,
        name=args.name,
        version=args.version,
        host=args.host,
        port=args.port,
        description=args.description,
        is_dark=not args.light,
        cdn_base=args.cdn,
        marketing_url=args.marketing_url,
        dock_icon=dock_icon,
    )

    theme_css = build_theme_css(vars_map, extra_css=extra_css)
    (out / meta.css_filename).write_text(theme_css, encoding="utf-8")

    ext = build_ext_json(meta)
    (out / meta.ext_filename).write_text(json.dumps(ext, indent=2) + "\n", encoding="utf-8")

    print(f"[ok] Wrote: {out / meta.css_filename}")
    print(f"[ok] Wrote: {out / meta.ext_filename}")
    if meta.cdn_base:
        base = meta.cdn_base.rstrip("/")
        print(f"[install] Paste into Standard Notes → Manage Plugins → Install:")
        print(f"          {base}/{meta.ext_filename}")
    else:
        print(f"[import] ext.json: http://{meta.host}:{meta.port}/{meta.ext_filename}")
        print(f"[import] theme.css: http://{meta.host}:{meta.port}/{meta.css_filename}")

    if args.serve:
        serve_directory(out, host=meta.host, port=meta.port)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
