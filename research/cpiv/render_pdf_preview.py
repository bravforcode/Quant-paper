"""Render a PDF contact sheet to an explicit, task-scoped output path."""

from __future__ import annotations

import argparse
from math import ceil
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = pymupdf.open(args.pdf)
    columns, cell_width, cell_height = 2, 420, 500
    rows = ceil(len(document) / columns)
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#e9edf1")
    draw = ImageDraw.Draw(sheet)
    for index, page in enumerate(document):
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(0.55, 0.55), alpha=False)
        thumbnail = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        column, row = index % columns, index // columns
        x = column * cell_width + (cell_width - thumbnail.width) // 2
        y = row * cell_height + 30
        draw.text(
            (column * cell_width + 12, row * cell_height + 8), f"Page {index + 1}", fill="black"
        )
        sheet.paste(thumbnail, (x, y))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)


if __name__ == "__main__":
    main()
