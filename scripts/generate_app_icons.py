#!/usr/bin/env python3
"""Generate iOS AppIcon PNGs from a single SVG or PNG source.

Requirements:
  pip install cairosvg pillow

Usage:
  python scripts/generate_app_icons.py path/to/source.svg \
         LeenVibe-iOS/LeenVibe/Resources/Assets.xcassets/AppIcon.appiconset

If the source file is PNG (ideally 1024×1024), the script will resize with Pillow.
If the source is SVG, it will be rasterised with CairoSVG first then resized.
"""
import sys
import os
from pathlib import Path

SIZES = {
    "icon_20@2x.png": 40,
    "icon_20@3x.png": 60,
    "icon_29@2x.png": 58,
    "icon_29@3x.png": 87,
    "icon_40@2x.png": 80,
    "icon_40@3x.png": 120,
    "icon_60@2x.png": 120,
    "icon_60@3x.png": 180,
    "icon_20_ipad@1x.png": 20,
    "icon_20_ipad@2x.png": 40,
    "icon_29_ipad@1x.png": 29,
    "icon_29_ipad@2x.png": 58,
    "icon_40_ipad@1x.png": 40,
    "icon_40_ipad@2x.png": 80,
    "icon_76@1x.png": 76,
    "icon_76@2x.png": 152,
    "icon_83.5@2x.png": 167,
    "icon_1024.png": 1024,
}

def ensure_deps():
    try:
        import cairosvg  # noqa: F401
    except ImportError:
        print("[ERROR] CairoSVG not installed. Please `pip install cairosvg pillow`. Exiting.")
        sys.exit(1)
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("[ERROR] Pillow not installed. Please `pip install pillow`. Exiting.")
        sys.exit(1)


def rasterise_svg(source: Path, size: int):
    import cairosvg
    from io import BytesIO
    png_bytes = cairosvg.svg2png(url=str(source), output_width=size, output_height=size)
    from PIL import Image
    return Image.open(BytesIO(png_bytes))


def resize_png(source: Path, size: int):
    from PIL import Image
    img = Image.open(source).convert("RGBA")
    return img.resize((size, size), Image.LANCZOS)


def main():
    if len(sys.argv) != 3:
        print("Usage: generate_app_icons.py <source.svg|png> <destination_appiconset_dir>")
        sys.exit(1)

    source = Path(sys.argv[1]).expanduser().resolve()
    dest_dir = Path(sys.argv[2]).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    ensure_deps()
    is_svg = source.suffix.lower() == ".svg"

    for filename, size in SIZES.items():
        out_path = dest_dir / filename
        if is_svg:
            img = rasterise_svg(source, size)
        else:
            img = resize_png(source, size)
        img.save(out_path, format="PNG")
        print(f"[✓] Wrote {out_path} ({size}x{size})")

    print("\nAll icons generated. Add the AppIcon set to your Xcode target if not already registered.")

if __name__ == "__main__":
    main() 