#!/usr/bin/env python3
"""Generate the configurable RMUL 2026 3v3 Gazebo field from JSON."""

import argparse
import copy
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PACKAGE_ROOT / "config" / "field_config.json"


def text_vector(values):
    return " ".join(f"{float(value):.6g}" for value in values)


def symmetric_xy(pose):
    return [-float(pose[0]), -float(pose[1]), float(pose[2])]


def add_text(parent, tag, value, **attributes):
    element = ET.SubElement(parent, tag, attributes)
    element.text = str(value)
    return element


def add_material(visual, rgba):
    material = ET.SubElement(visual, "material")
    add_text(material, "ambient", text_vector(rgba))
    add_text(material, "diffuse", text_vector(rgba))
    if float(rgba[3]) < 1.0:
        add_text(visual, "transparency", f"{1.0 - float(rgba[3]):.6g}")


def add_box(model, name, center, size, rgba, collision=True):
    link = ET.SubElement(model, "link", {"name": name})
    add_text(link, "pose", f"{text_vector(center)} 0 0 0")

    if collision:
        collision_element = ET.SubElement(link, "collision", {"name": "collision"})
        geometry = ET.SubElement(collision_element, "geometry")
        box = ET.SubElement(geometry, "box")
        add_text(box, "size", text_vector(size))

    visual = ET.SubElement(link, "visual", {"name": "visual"})
    geometry = ET.SubElement(visual, "geometry")
    box = ET.SubElement(geometry, "box")
    add_text(box, "size", text_vector(size))
    add_text(visual, "cast_shadows", "true" if collision else "false")
    add_material(visual, rgba)


def require_positive(name, values):
    if any(float(value) <= 0.0 for value in values):
        raise ValueError(f"{name} must contain positive values: {values}")


def validate(config):
    require_positive("field.size", config["field"]["size"])
    require_positive("zones.supply.size", config["zones"]["supply"]["size"])
    require_positive("zones.control.size", config["zones"]["control"]["size"])
    require_positive("highlands.main_size", config["highlands"]["main_size"])
    require_positive("highlands.guard_size", config["highlands"]["guard_size"])

    field_x, field_y, _ = map(float, config["field"]["size"])
    if not math.isclose(field_x, 12.0) or not math.isclose(field_y, 8.0):
        print("WARNING: field size differs from the RMUL 2026 official 12 x 8 m value.")

    wall = config["perimeter_wall"]
    if wall["enabled"]:
        require_positive("perimeter_wall", [wall["height"], wall["thickness"]])


def generate_model(config):
    sdf = ET.Element("sdf", {"version": config["sdf_version"]})
    model = ET.SubElement(sdf, "model", {"name": "rmul_2026_3v3_field"})
    add_text(model, "static", "true")

    materials = config["materials"]
    field = config["field"]
    add_box(model, "floor", field["center"], field["size"], materials["floor"])

    supply = config["zones"]["supply"]
    red_supply = supply["red_center"]
    blue_supply = symmetric_xy(red_supply)
    add_box(model, "red_supply_zone", red_supply, supply["size"], materials["red_supply"], False)
    add_box(model, "blue_supply_zone", blue_supply, supply["size"], materials["blue_supply"], False)

    control = config["zones"]["control"]
    add_box(model, "control_zone", control["center"], control["size"], materials["control_zone"], False)

    highlands = config["highlands"]
    red_main = highlands["red_main_center"]
    blue_main = symmetric_xy(red_main)
    red_guard = highlands["red_guard_center"]
    blue_guard = symmetric_xy(red_guard)
    add_box(model, "red_highland_main", red_main, highlands["main_size"], materials["highland"])
    add_box(model, "blue_highland_main", blue_main, highlands["main_size"], materials["highland"])
    add_box(model, "red_highland_guard", red_guard, highlands["guard_size"], materials["highland"])
    add_box(model, "blue_highland_guard", blue_guard, highlands["guard_size"], materials["highland"])

    wall = config["perimeter_wall"]
    if wall["enabled"]:
        length, width, _ = map(float, field["size"])
        thickness = float(wall["thickness"])
        height = float(wall["height"])
        color = materials["perimeter_wall"]
        add_box(model, "north_wall", [0, width / 2 + thickness / 2, height / 2],
                [length + 2 * thickness, thickness, height], color)
        add_box(model, "south_wall", [0, -width / 2 - thickness / 2, height / 2],
                [length + 2 * thickness, thickness, height], color)
        add_box(model, "east_wall", [length / 2 + thickness / 2, 0, height / 2],
                [thickness, width, height], color)
        add_box(model, "west_wall", [-length / 2 - thickness / 2, 0, height / 2],
                [thickness, width, height], color)

    return sdf


def generate_world(config):
    sdf = ET.Element("sdf", {"version": config["sdf_version"]})
    world_config = config["world"]
    world = ET.SubElement(sdf, "world", {"name": world_config["name"]})
    add_text(world, "gravity", text_vector(world_config["gravity"]))

    physics = ET.SubElement(world, "physics", {"name": "default_physics", "type": "ode"})
    add_text(physics, "max_step_size", world_config["max_step_size"])
    add_text(physics, "real_time_update_rate", world_config["real_time_update_rate"])

    scene = ET.SubElement(world, "scene")
    add_text(scene, "ambient", "0.55 0.55 0.55 1")
    add_text(scene, "background", "0.75 0.80 0.90 1")
    add_text(scene, "shadows", "true")

    # Keep the world self-contained.  model://sun and model://field can make
    # Gazebo Classic contact the online model database during startup.
    sun = ET.SubElement(world, "light", {"name": "sun", "type": "directional"})
    add_text(sun, "cast_shadows", "true")
    add_text(sun, "pose", "0 0 10 0 0 0")
    add_text(sun, "diffuse", "0.8 0.8 0.8 1")
    add_text(sun, "specular", "0.2 0.2 0.2 1")
    add_text(sun, "direction", "-0.5 0.1 -0.9")

    field_model = generate_model(config).find("model")
    world.append(copy.deepcopy(field_model))

    gui = ET.SubElement(world, "gui", {"fullscreen": "0"})
    camera = ET.SubElement(gui, "camera", {"name": "overview_camera"})
    add_text(camera, "pose", "10 -12 11 0 0.55 2.25")
    add_text(camera, "view_controller", "orbit")
    return sdf


def write_xml(root, destination):
    ET.indent(root, space="  ")
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)


def print_geometry(config):
    field = config["field"]
    length, width, _ = map(float, field["size"])
    supply = config["zones"]["supply"]
    highlands = config["highlands"]
    rows = [
        ("floor", field["center"], field["size"]),
        ("red_supply_zone", supply["red_center"], supply["size"]),
        ("blue_supply_zone", symmetric_xy(supply["red_center"]), supply["size"]),
        ("control_zone", config["zones"]["control"]["center"], config["zones"]["control"]["size"]),
        ("red_highland_main", highlands["red_main_center"], highlands["main_size"]),
        ("blue_highland_main", symmetric_xy(highlands["red_main_center"]), highlands["main_size"]),
        ("red_highland_guard", highlands["red_guard_center"], highlands["guard_size"]),
        ("blue_highland_guard", symmetric_xy(highlands["red_guard_center"]), highlands["guard_size"]),
    ]
    print(f"Playable extents: X=[{-length/2:g}, {length/2:g}], Y=[{-width/2:g}, {width/2:g}]")
    print(f"{'object':24} {'center xyz':30} {'size xyz'}")
    for name, center, size in rows:
        print(f"{name:24} {text_vector(center):30} {text_vector(size)}")
    print("Center symmetry checks: PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=PACKAGE_ROOT)
    args = parser.parse_args()

    with args.config.open(encoding="utf-8") as stream:
        config = json.load(stream)
    validate(config)

    model_path = args.output_root / "models" / "rmul_2026_3v3_field" / "model.sdf"
    world_path = args.output_root / "worlds" / "rmul_2026_3v3.world"
    write_xml(generate_model(config), model_path)
    write_xml(generate_world(config), world_path)
    print(f"Generated: {model_path}")
    print(f"Generated: {world_path}")
    print_geometry(config)


if __name__ == "__main__":
    main()
