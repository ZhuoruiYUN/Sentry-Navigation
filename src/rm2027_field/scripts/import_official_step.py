#!/usr/bin/env python3
"""Convert the official RMUL 2027 STEP field to colored Gazebo STL assets."""

import argparse
from collections import defaultdict
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "rmul_2027_3v3_official"
SOURCE = PACKAGE_ROOT / "sources" / "RMUL2027_3V3_V1.0.0.stp"


def world_point(cad):
    """STEP millimetres (negative Y up) to the field frame (red at -X, +Y)."""
    return (-cad[0] / 1000.0, -cad[2] / 1000.0, -cad[1] / 1000.0)


def normal(a, b, c):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1],
         u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    length = math.sqrt(sum(x * x for x in n))
    return tuple(x / length for x in n) if length else (0.0, 0.0, 1.0)


def write_stl(path, triangles):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(path.stem.encode("ascii")[:80].ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(triangles)))
        for a, b, c in triangles:
            values = (*normal(a, b, c), *a, *b, *c)
            stream.write(struct.pack("<12fH", *values, 0))


def add_text(parent, name, value):
    item = ET.SubElement(parent, name)
    item.text = str(value)
    return item


def add_mesh(parent, filename):
    geometry = ET.SubElement(parent, "geometry")
    mesh = ET.SubElement(geometry, "mesh")
    add_text(mesh, "uri", f"model://{MODEL_NAME}/meshes/{filename}")


def write_model(output_root, color_triangles):
    sdf = ET.Element("sdf", {"version": "1.7"})
    model = ET.SubElement(sdf, "model", {"name": MODEL_NAME})
    add_text(model, "static", "true")
    link = ET.SubElement(model, "link", {"name": "field"})
    collision = ET.SubElement(link, "collision", {"name": "official_geometry"})
    add_mesh(collision, "collision.stl")
    for color in sorted(color_triangles):
        filename = "color_" + "".join(f"{value:02x}" for value in color[:3]) + ".stl"
        visual = ET.SubElement(link, "visual", {"name": filename[:-4]})
        add_mesh(visual, filename)
        material = ET.SubElement(visual, "material")
        rgba = [value / 255.0 for value in color]
        add_text(material, "ambient", " ".join(f"{value:.6g}" for value in rgba))
        add_text(material, "diffuse", " ".join(f"{value:.6g}" for value in rgba))
        add_text(visual, "cast_shadows", "true")

    model_dir = output_root / "models" / MODEL_NAME
    model_dir.mkdir(parents=True, exist_ok=True)
    ET.indent(sdf, space="  ")
    ET.ElementTree(sdf).write(model_dir / "model.sdf", encoding="utf-8", xml_declaration=True)
    (model_dir / "model.config").write_text(
        '<?xml version="1.0"?>\n<model>\n'
        '  <name>RMUL 2027 3v3 Official Field</name>\n'
        '  <version>1.0</version>\n'
        '  <sdf version="1.7">model.sdf</sdf>\n'
        '  <description>Official 2027 STEP field converted to Gazebo meshes.</description>\n'
        '</model>\n', encoding="utf-8")


def write_world(output_root):
    template = ET.parse(PACKAGE_ROOT / "worlds" / "rmul_2027_3v3.world")
    world = template.getroot().find("world")
    world.set("name", "rmul_2027_3v3")
    for element in list(world):
        if element.tag in {"model", "include"}:
            world.remove(element)
    include = ET.Element("include")
    add_text(include, "uri", f"model://{MODEL_NAME}")
    world.insert(3, include)
    camera = world.find("gui/camera/pose")
    if camera is not None:
        camera.text = "-8 -9 11 0 0.72 0.85"
    ET.indent(template.getroot(), space="  ")
    (output_root / "worlds").mkdir(parents=True, exist_ok=True)
    template.write(output_root / "worlds" / "rmul_2027_3v3.world",
                   encoding="utf-8", xml_declaration=True)


def convert(step_path, output_root):
    try:
        import gmsh
    except ImportError as exc:
        raise SystemExit("Install python3-gmsh to regenerate the official meshes.") from exc
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.open(str(step_path))
        gmsh.model.mesh.generate(2)
        tags, coordinates, _ = gmsh.model.mesh.getNodes()
        points = {int(tag): world_point(coordinates[3 * i:3 * i + 3])
                  for i, tag in enumerate(tags)}
        all_triangles = []
        colored = defaultdict(list)
        for _, surface_tag in gmsh.model.getEntities(2):
            red, green, blue, alpha = gmsh.model.getColor(2, surface_tag)
            # The STEP base has unset colors (alpha=0). Render those faces as
            # neutral gray; preserve every explicit CAD surface color.
            color = (red, green, blue, alpha) if alpha else (120, 125, 130, 255)
            element_types, _, node_groups = gmsh.model.mesh.getElements(2, surface_tag)
            for element_type, node_group in zip(element_types, node_groups):
                if int(element_type) != 2:
                    raise ValueError(f"Unexpected surface element type: {element_type}")
                for offset in range(0, len(node_group), 3):
                    a, b, c = (points[int(node_group[offset + i])] for i in (0, 1, 2))
                    triangle = (a, b, c)
                    colored[color].append(triangle)
                    all_triangles.append(triangle)
        if not all_triangles:
            raise ValueError("The STEP import produced no surface triangles")
        low = [min(vertex[i] for tri in all_triangles for vertex in tri) for i in range(3)]
        high = [max(vertex[i] for tri in all_triangles for vertex in tri) for i in range(3)]
        sizes = [high[i] - low[i] for i in range(3)]
        if not (12.5 < sizes[0] < 12.7 and 8.5 < sizes[1] < 8.7
                and -0.11 < low[2] < -0.09 and 0.40 < high[2] < 0.45):
            raise ValueError(f"Unexpected transformed field bounds: {low}, {high}")
        mesh_dir = output_root / "models" / MODEL_NAME / "meshes"
        write_stl(mesh_dir / "collision.stl", all_triangles)
        for color, triangles in colored.items():
            filename = "color_" + "".join(f"{value:02x}" for value in color[:3]) + ".stl"
            write_stl(mesh_dir / filename, triangles)
        write_model(output_root, colored)
        write_world(output_root)
        print(f"Official STEP: {len(all_triangles)} triangles, {len(colored)} colors")
        print(f"World bounds (m): {low} to {high}")
    finally:
        gmsh.finalize()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path, default=SOURCE)
    parser.add_argument("--output-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()
    convert(args.step, args.output_root)


if __name__ == "__main__":
    main()
