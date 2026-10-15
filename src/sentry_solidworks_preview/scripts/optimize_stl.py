"""Make a smaller visual STL from a SolidWorks binary STL using vertex clustering.

Requires NumPy. This is for visual preview meshes, not collision geometry.
"""

import argparse
import struct
from pathlib import Path

import numpy as np


TRIANGLE = np.dtype(
    [("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")]
)


def optimize(source: Path, destination: Path, voxel: float) -> None:
    with source.open("rb") as stream:
        stream.seek(80)
        count = struct.unpack("<I", stream.read(4))[0]
    triangles = np.fromfile(source, dtype=TRIANGLE, offset=84)
    if len(triangles) != count:
        raise ValueError(f"Invalid binary STL: {source}")

    vertices = triangles["vertices"].reshape(-1, 3)
    cells = np.rint(vertices / voxel).astype(np.int32)
    _, indices = np.unique(cells, axis=0, return_inverse=True)
    size = int(indices.max()) + 1
    cluster_counts = np.bincount(indices, minlength=size)
    points = np.column_stack(
        [
            np.bincount(indices, weights=vertices[:, axis], minlength=size)
            / cluster_counts
            for axis in range(3)
        ]
    )

    faces = indices.reshape(-1, 3)
    valid = (
        (faces[:, 0] != faces[:, 1])
        & (faces[:, 1] != faces[:, 2])
        & (faces[:, 0] != faces[:, 2])
    )
    face_vertices = points[faces[valid]].astype("<f4")
    normals = np.cross(
        face_vertices[:, 1] - face_vertices[:, 0],
        face_vertices[:, 2] - face_vertices[:, 0],
    )
    lengths = np.linalg.norm(normals, axis=1)
    nonzero = lengths > 0
    normals[nonzero] /= lengths[nonzero, None]
    normals[~nonzero] = 0

    result = np.zeros(len(face_vertices), dtype=TRIANGLE)
    result["normal"] = normals
    result["vertices"] = face_vertices
    with destination.open("wb") as stream:
        stream.write(f"Visual preview, voxel={voxel} m".encode().ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(result)))
        result.tofile(stream)
    print(f"{source.name}: {count:,} -> {len(result):,} triangles")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--voxel", type=float, required=True)
    args = parser.parse_args()
    optimize(args.source, args.destination, args.voxel)
