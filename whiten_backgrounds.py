"""Give every product photo a white background.

73 of the 102 catalogue photos were saved with a black background (transparent PNGs flattened
to JPG). This flood-fills the near-black region connected to the image border, feathers the
edge, and composites the product onto white. Photos that are already white are copied as-is.

Originals are kept in data/products_original/ (and in data.zip); the site keeps serving
data/products/, so the image_file_path values in the database don't change.

Run:  .venv\\Scripts\\python.exe whiten_backgrounds.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

APP_DIR = Path(__file__).resolve().parent
PRODUCTS = APP_DIR / "data" / "products"
ORIGINALS = APP_DIR / "data" / "products_original"
DARK = 18  # max channel value treated as background black (the backgrounds are 0-10)
LIGHT = 232  # min channel value treated as background white


def border_connected(region: np.ndarray) -> np.ndarray:
    """Keep only the parts of a boolean region that touch the image border."""
    labels, _ = ndimage.label(region)
    border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    return np.isin(labels, np.unique(border[border > 0]))


def background_mask(rgb: np.ndarray) -> np.ndarray:
    """True where a pixel is background (near-black, or off-white beside it) connected to the border.

    Some photos are white with black bars on the sides; the off-white background and the
    thin JPEG seam between the two are included so no faint gray line is left behind.
    """
    dark = border_connected(rgb.max(axis=2) <= DARK)
    if not dark.any():
        return dark
    light = border_connected(rgb.min(axis=2) >= LIGHT)
    return ndimage.binary_closing(dark | light, iterations=2) | dark | light


def whiten(src: Path, dst: Path) -> float:
    """Write a white-background copy of src to dst; return the share of pixels replaced."""
    img = Image.open(src).convert("RGB")
    rgb = np.asarray(img)
    mask = background_mask(rgb)
    if not mask.any():
        shutil.copy2(src, dst)
        return 0.0
    # Grow the mask 1px to swallow the dark JPEG halo, then soften it so edges blend.
    mask = ndimage.binary_dilation(mask, iterations=1)
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
    white = Image.new("RGB", img.size, (255, 255, 255))
    Image.composite(white, img, alpha).save(dst, quality=92)
    return float(mask.mean())


def main() -> int:
    if not ORIGINALS.exists():
        shutil.copytree(PRODUCTS, ORIGINALS)
        print(f"Backed up originals to {ORIGINALS.relative_to(APP_DIR)}")
    changed = 0
    for src in sorted(ORIGINALS.glob("*.jpg")):
        share = whiten(src, PRODUCTS / src.name)
        if share:
            changed += 1
            print(f"whitened {share:6.1%}  {src.name}")
    print(f"\n{changed} photos whitened, {len(list(ORIGINALS.glob('*.jpg'))) - changed} already white")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
