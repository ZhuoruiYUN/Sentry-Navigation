#!/usr/bin/env python3
"""Mark raised STEP field geometry as occupied in a saved 2-D SLAM map.

The sentry's Gazebo planar-motion plugin keeps it at ground height and does
not resolve rigid-body contacts. A lidar map alone can miss the broad top of
the 2027 highlands, allowing Nav2 to route through their visual geometry.
Keep the SLAM map as the input; write a separate map for navigation.
"""

import argparse
import ast
import math
from pathlib import Path
import re
import struct


WORKSPACE = Path(__file__).resolve().parents[3]
DEFAULT_MAP = WORKSPACE / "maps/rmul_2027_3v3.yaml"
DEFAULT_MESH = (
    WORKSPACE
    / "src/rm2027_field/models/rmul_2027_3v3_official/meshes/collision.stl"
)
DEFAULT_OUTPUT = WORKSPACE / "maps/rmul_2027_3v3_nav.yaml"


def read_pgm(path):
    with path.open("rb") as stream:
        def token():
            while True:
                char = stream.read(1)
                if not char:
                    raise ValueError("Incomplete PGM header")
                if char == b"#":
                    stream.readline()
                elif not char.isspace():
                    break
            value = bytearray(char)
            while True:
                char = stream.read(1)
                if not char or char.isspace():
                    return bytes(value)
                value.extend(char)

        magic = token()
        width, height, maxval = (int(token()) for _ in range(3))
        if magic != b"P5" or maxval != 255:
            raise ValueError("Expected an 8-bit binary PGM (P5) map")
        pixels = bytearray(stream.read())
        if len(pixels) != width * height:
            raise ValueError("PGM pixel count does not match its dimensions")
    return width, height, pixels


def projected_triangles(mesh_path, minimum_height):
    with mesh_path.open("rb") as stream:
        stream.read(80)
        count_bytes = stream.read(4)
        if len(count_bytes) != 4:
            raise ValueError("Incomplete binary STL header")
        count = struct.unpack("<I", count_bytes)[0]
        for _ in range(count):
            record = stream.read(50)
            if len(record) != 50:
                raise ValueError("Incomplete binary STL triangle")
            values = struct.unpack("<12fH", record)
            vertices = [values[3:6], values[6:9], values[9:12]]
            # Top surfaces fill solid highlands, workbenches and tunnel plates.
            # Ground paint and the arena floor remain traversable.
            if min(vertex[2] for vertex in vertices) >= minimum_height:
                yield [(vertex[0], vertex[1]) for vertex in vertices]


def mark_triangle(pixels, width, height, origin, resolution, vertices):
    x0, y0 = origin[:2]
    xs = [point[0] for point in vertices]
    ys = [point[1] for point in vertices]
    left = max(0, math.floor((min(xs) - x0) / resolution) - 1)
    right = min(width - 1, math.ceil((max(xs) - x0) / resolution))
    top = max(0, height - 1 - math.ceil((max(ys) - y0) / resolution))
    bottom = min(height - 1, height - math.floor((min(ys) - y0) / resolution))
    if left > right or top > bottom:
        return 0

    (ax, ay), (bx, by), (cx, cy) = vertices
    area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if abs(area) < 1e-12:
        return 0
    sign = 1 if area > 0 else -1
    added = 0
    for row in range(top, bottom + 1):
        y = y0 + (height - row - 0.5) * resolution
        for col in range(left, right + 1):
            x = x0 + (col + 0.5) * resolution
            e0 = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
            e1 = (cx - bx) * (y - by) - (cy - by) * (x - bx)
            e2 = (ax - cx) * (y - cy) - (ay - cy) * (x - cx)
            if min(sign * e0, sign * e1, sign * e2) >= -1e-9:
                index = row * width + col
                if pixels[index] != 0:
                    pixels[index] = 0
                    added += 1
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--mesh", type=Path, default=DEFAULT_MESH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--minimum-height", type=float, default=0.15)
    args = parser.parse_args()

    source_text = args.map.read_text()
    image_match = re.search(r"(?m)^image:\s*(\S+)\s*$", source_text)
    resolution_match = re.search(r"(?m)^resolution:\s*([\d.]+)\s*$", source_text)
    origin_match = re.search(r"(?m)^origin:\s*(\[[^\n]+\])\s*$", source_text)
    if not all((image_match, resolution_match, origin_match)):
        raise ValueError("Map YAML needs image, resolution and origin fields")
    image_path = args.map.parent / image_match.group(1)
    resolution = float(resolution_match.group(1))
    origin = ast.literal_eval(origin_match.group(1))
    if resolution <= 0 or len(origin) < 2:
        raise ValueError("Invalid map resolution or origin")
    width, height, pixels = read_pgm(image_path)

    changed = 0
    for triangle in projected_triangles(args.mesh, args.minimum_height):
        changed += mark_triangle(pixels, width, height, origin, resolution, triangle)

    output_image = args.output.with_suffix(".pgm")
    output_image.write_bytes(f"P5\n{width} {height}\n255\n".encode() + pixels)
    output_text = source_text.replace(image_match.group(0), f"image: {output_image.name}", 1)
    args.output.write_text(output_text.rstrip() + "\n")
    print(f"Wrote {args.output} and {output_image}; marked {changed} raised-geometry cells occupied")


if __name__ == "__main__":
    main()
