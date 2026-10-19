from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


DEFAULT_SPRITE = Path("tu.png")
FRAME_NAMES = (
    "keyboard_ready",
    "keyboard_left_up",
    "keyboard_left_down",
    "keyboard_right_up",
    "keyboard_right_down",
    "game_ready",
    "game_wasd_up",
    "game_wasd_down",
    "game_mouse_move",
    "game_mouse_click",
)


def grid_boxes(width: int, height: int, cols: int, rows: int) -> list[tuple[int, int, int, int]]:
    x_edges = [round(width * i / cols) for i in range(cols + 1)]
    y_edges = [round(height * i / rows) for i in range(rows + 1)]
    return [
        (x_edges[col], y_edges[row], x_edges[col + 1], y_edges[row + 1])
        for row in range(rows)
        for col in range(cols)
    ]


def is_checker_background(pixel: tuple[int, int, int, int], min_light: int, max_chroma: int) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True
    return min(r, g, b) >= min_light and max(r, g, b) - min(r, g, b) <= max_chroma


def remove_checkerboard_background(
    image: Image.Image,
    min_light: int = 232,
    max_chroma: int = 28,
    cleanup_passes: int = 2,
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def index(x: int, y: int) -> int:
        return y * width + x

    def enqueue(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= width or y >= height:
            return
        idx = index(x, y)
        if visited[idx]:
            return
        if not is_checker_background(pixels[x, y], min_light, max_chroma):
            return
        visited[idx] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        enqueue(x + 1, y)
        enqueue(x - 1, y)
        enqueue(x, y + 1)
        enqueue(x, y - 1)

    for y in range(height):
        for x in range(width):
            if visited[index(x, y)]:
                r, g, b, _a = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)

    # Pick off tiny checkerboard leftovers connected to newly transparent pixels,
    # but do not globally delete white sleeve highlights.
    for _ in range(cleanup_passes):
        to_clear: list[tuple[int, int]] = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if pixels[x, y][3] == 0:
                    continue
                if not is_checker_background(pixels[x, y], min_light, max_chroma):
                    continue
                if (
                    pixels[x + 1, y][3] == 0
                    or pixels[x - 1, y][3] == 0
                    or pixels[x, y + 1][3] == 0
                    or pixels[x, y - 1][3] == 0
                ):
                    to_clear.append((x, y))
        for x, y in to_clear:
            r, g, b, _a = pixels[x, y]
            pixels[x, y] = (r, g, b, 0)

    return rgba


def split_tu_sprite(
    sprite_path: Path,
    output_dir: Path,
    cols: int = 5,
    rows: int = 2,
    min_light: int = 220,
    max_chroma: int = 36,
) -> list[Path]:
    sprite = Image.open(sprite_path).convert("RGBA")
    boxes = grid_boxes(sprite.width, sprite.height, cols, rows)
    if len(boxes) != len(FRAME_NAMES):
        raise ValueError(f"Expected {len(FRAME_NAMES)} cells, got {len(boxes)}")

    target_width = max(x1 - x0 for x0, _y0, x1, _y1 in boxes)
    target_height = max(y1 - y0 for _x0, y0, _x1, y1 in boxes)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_png in output_dir.glob("*.png"):
        stale_png.unlink()

    written: list[Path] = []
    for frame_name, box in zip(FRAME_NAMES, boxes):
        cell = sprite.crop(box)
        normalized = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        normalized.alpha_composite(cell, (0, 0))
        transparent = remove_checkerboard_background(normalized, min_light=min_light, max_chroma=max_chroma)
        out_path = output_dir / f"{frame_name}.png"
        transparent.save(out_path)
        written.append(out_path)

    return written


def write_preview(frame_paths: list[Path], preview_path: Path, cols: int = 5) -> None:
    frames = [Image.open(path).convert("RGBA") for path in frame_paths]
    if not frames:
        return
    cell_width = max(frame.width for frame in frames)
    cell_height = max(frame.height for frame in frames)
    rows = (len(frames) + cols - 1) // cols
    preview = Image.new("RGBA", (cell_width * cols, cell_height * rows), (42, 44, 48, 255))
    draw = ImageDraw.Draw(preview, "RGBA")

    tile = 18
    for y in range(0, preview.height, tile):
        for x in range(0, preview.width, tile):
            color = (54, 57, 63, 255) if (x // tile + y // tile) % 2 else (33, 35, 39, 255)
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=color)

    for index, frame in enumerate(frames):
        x = (index % cols) * cell_width
        y = (index // cols) * cell_height
        preview.alpha_composite(frame, (x, y))

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview.convert("RGB").save(preview_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Split tu.png into transparent desktop pet frames.")
    parser.add_argument("--sprite", type=Path, default=DEFAULT_SPRITE, help="Path to the 2x5 sprite sheet.")
    parser.add_argument("--output-dir", type=Path, default=Path("assets/frames"), help="Where transparent frames are written.")
    parser.add_argument("--preview", type=Path, default=Path("assets/frames_preview.png"), help="Preview image path.")
    parser.add_argument("--min-light", type=int, default=220, help="Minimum RGB value treated as checkerboard background.")
    parser.add_argument("--max-chroma", type=int, default=36, help="Maximum RGB channel spread treated as neutral background.")
    args = parser.parse_args()

    frame_paths = split_tu_sprite(
        args.sprite,
        args.output_dir,
        min_light=args.min_light,
        max_chroma=args.max_chroma,
    )
    write_preview(frame_paths, args.preview)

    print(f"Wrote {len(frame_paths)} transparent frames to: {args.output_dir.resolve()}")
    print(f"Wrote preview to: {args.preview.resolve()}")


if __name__ == "__main__":
    main()
