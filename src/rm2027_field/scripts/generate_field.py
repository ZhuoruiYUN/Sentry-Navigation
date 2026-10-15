#!/usr/bin/env python3
"""Generate the RMUL 2027 3v3 Gazebo field from the measured JSON layout."""

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


def add_box(model, name, center, size, rgba, collision=True, rpy=(0, 0, 0)):
    link = ET.SubElement(model, "link", {"name": name})
    add_text(link, "pose", f"{text_vector(center)} {text_vector(rpy)}")

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


def add_prism(model, name, center_xy, bottom_z, points, height, rgba, yaw=0):
    """Extrude a footprint, including real 50 mm corner cuts, for both render and collision."""
    link = ET.SubElement(model, "link", {"name": name})
    add_text(link, "pose", f"{text_vector([*center_xy, bottom_z])} 0 0 {yaw:.6g}")
    for tag in ("collision", "visual"):
        element = ET.SubElement(link, tag, {"name": tag})
        geometry = ET.SubElement(element, "geometry")
        polyline = ET.SubElement(geometry, "polyline")
        for point in points:
            add_text(polyline, "point", text_vector(point))
        add_text(polyline, "height", height)
        if tag == "visual":
            add_text(element, "cast_shadows", "true")
            add_material(element, rgba)


def chamfered_rectangle(width, depth, chamfer, north_only=False, south_only=False):
    x, y = width / 2, depth / 2
    south = chamfer if not north_only else 0
    north = chamfer if not south_only else 0
    points = [(-x + south, -y), (x - south, -y)]
    if south:
        points.append((x, -y + south))
    points.append((x, y - north))
    if north:
        points.extend([(x - north, y), (-x + north, y), (-x, y - north)])
    else:
        points.append((-x, y))
    if south:
        points.append((-x, -y + south))
    return points


def require_positive(name, values):
    if any(float(value) <= 0.0 for value in values):
        raise ValueError(f"{name} must contain positive values: {values}")


def validate(config):
    require_positive("field.size", config["field"]["size"])
    require_positive("zones.supply.size", config["zones"]["supply"]["size"])
    require_positive("zones.central_control.size", config["zones"]["central_control"]["size"])
    require_positive("zones.highland_control.size", config["zones"]["highland_control"]["size"])
    require_positive("workbench.size", config["workbench"]["size"])
    require_positive("workbench.chamfer", [config["workbench"]["chamfer"]])
    require_positive("highlands.main_size", config["highlands"]["main_size"])
    require_positive("highlands.guard_size", config["highlands"]["guard_size"])
    require_positive("tunnel.metal_plate_size", config["tunnel"]["metal_plate_size"])
    require_positive("tunnel.wall_barrier_size", config["tunnel"]["wall_barrier_size"])
    require_positive("tunnel.landing_depth", [config["tunnel"]["landing_depth"]])
    require_positive("tunnel.chamfer", [config["tunnel"]["chamfer"]])

    field_x, field_y, _ = map(float, config["field"]["size"])
    if not math.isclose(field_x, 12.0) or not math.isclose(field_y, 8.0):
        print("WARNING: field size differs from the RMUL 2027 official 12 x 8 m value.")

    supply = config["zones"]["supply"]
    sx, sy, _ = map(float, supply["size"])
    cx, cy, _ = map(float, supply["red_center"])
    if not (math.isclose(cx - sx / 2, -field_x / 2)
            and math.isclose(cy + sy / 2, field_y / 2)):
        raise ValueError("red supply zone must occupy the north-west field corner")

    bench = config["workbench"]
    bx, by, _ = map(float, bench["red_center"])
    bw, bd, _ = map(float, bench["size"])
    if (bx - bw / 2 < cx - sx / 2 or bx + bw / 2 > cx + sx / 2
            or by - bd / 2 < cy - sy / 2 or by + bd / 2 > cy + sy / 2):
        raise ValueError("red workbench must fit within the supply zone")
    if 2 * float(bench["chamfer"]) >= min(bw, bd):
        raise ValueError("workbench chamfer must fit within its footprint")

    highland = config["highlands"]
    _, main_length, _ = map(float, highland["main_size"])
    red_main_y = float(highland["red_main_center"][1])
    gap = field_y / 2 - (red_main_y + main_length / 2)
    tunnel = config["tunnel"]
    if not math.isclose(gap, float(tunnel["gap_to_perimeter"]), abs_tol=1e-6):
        raise ValueError("highland north end must leave the specified tunnel gap")
    main_width = float(highland["main_size"][0])
    plate_width = float(tunnel["metal_plate_size"][0])
    passage_width = float(tunnel["passage_width_each_side"])
    if not math.isclose(plate_width + 2 * passage_width, main_width, abs_tol=1e-6):
        raise ValueError("metal plate plus two passages must span the highland width")
    if not math.isclose(float(tunnel["metal_plate_size"][1]), gap, abs_tol=1e-6):
        raise ValueError("metal plate length must span the tunnel gap")
    if not math.isclose(float(tunnel["wall_barrier_size"][0]), main_width, abs_tol=1e-6):
        raise ValueError("wall-side tunnel barrier must span the highland width")
    if 2 * float(tunnel["chamfer"]) >= float(tunnel["wall_barrier_size"][1]):
        raise ValueError("tunnel chamfer must fit within the wall-side barrier")
    if float(tunnel["highland_bridge_top_z"]) <= float(highland["main_size"][2]):
        raise ValueError("highland bridge landing must rise above the highland")

    wall = config["perimeter_wall"]
    if wall["enabled"]:
        require_positive("perimeter_wall", [wall["height"], wall["thickness"]])


def generate_model(config):
    sdf = ET.Element("sdf", {"version": config["sdf_version"]})
    model = ET.SubElement(sdf, "model", {"name": config["model"]["name"]})
    add_text(model, "static", "true")

    materials = config["materials"]
    field = config["field"]
    add_box(model, "floor", field["center"], field["size"], materials["floor"])

    supply = config["zones"]["supply"]
    red_supply = supply["red_center"]
    blue_supply = symmetric_xy(red_supply)
    add_box(model, "red_supply_zone", red_supply, supply["size"], materials["red_supply"], False)
    add_box(model, "blue_supply_zone", blue_supply, supply["size"], materials["blue_supply"], False)

    control = config["zones"]["central_control"]
    add_box(model, "central_control_zone", control["center"], control["size"],
            materials["central_control"], False)

    highlands = config["highlands"]
    red_main = highlands["red_main_center"]
    blue_main = symmetric_xy(red_main)
    red_guard = highlands["red_guard_center"]
    blue_guard = symmetric_xy(red_guard)
    main_width, main_length, main_height = map(float, highlands["main_size"])
    nose = chamfered_rectangle(main_width, main_length,
                               float(config["tunnel"]["chamfer"]), north_only=True)
    add_prism(model, "red_highland_main", red_main[:2], 0, nose, main_height,
              materials["highland"])
    add_prism(model, "blue_highland_main", blue_main[:2], 0, nose, main_height,
              materials["highland"], math.pi)
    add_box(model, "red_highland_guard", red_guard, highlands["guard_size"], materials["highland"])
    add_box(model, "blue_highland_guard", blue_guard, highlands["guard_size"], materials["highland"])

    highland_control = config["zones"]["highland_control"]
    red_control = highland_control["red_center"]
    add_box(model, "red_highland_control_zone", red_control, highland_control["size"],
            materials["highland_control"], False)
    add_box(model, "blue_highland_control_zone", symmetric_xy(red_control),
            highland_control["size"], materials["highland_control"], False)

    bench = config["workbench"]
    red_bench = bench["red_center"]
    bench_width, bench_depth, bench_height = map(float, bench["size"])
    bench_shape = chamfered_rectangle(bench_width, bench_depth, float(bench["chamfer"]))
    add_prism(model, "red_workbench", red_bench[:2], 0, bench_shape, bench_height,
              materials["workbench"])
    add_prism(model, "blue_workbench", symmetric_xy(red_bench)[:2], 0, bench_shape,
              bench_height, materials["workbench"], math.pi)

    tunnel = config["tunnel"]
    red_tunnel_x, red_tunnel_y = map(float, tunnel["red_center_xy"])
    plate_width, gap, plate_thickness = map(float, tunnel["metal_plate_size"])
    wall_width, wall_depth, wall_height = map(float, tunnel["wall_barrier_size"])
    wall_top = wall_height
    highland_top = float(tunnel["highland_bridge_top_z"])
    # The bridge joins the floor-to-top wall-side barrier and the raised landing on the
    # highland. A slight pitch matches the 250 / 270 mm end heights in Fig 3-8.
    slope = math.atan2(highland_top - wall_top, gap)
    bridge_center_z = (wall_top + highland_top) / 2 - plate_thickness / 2
    bridge_center = [red_tunnel_x, red_tunnel_y, bridge_center_z]
    for side, yaw, center in (("red", 0, bridge_center),
                              ("blue", math.pi, symmetric_xy(bridge_center))):
        add_box(model, f"{side}_tunnel_bridge", center, tunnel["metal_plate_size"],
                materials["metal_plate"], rpy=(-slope, 0, yaw))
        direction = 1 if side == "red" else -1
        wall_center_y = direction * (float(config["field"]["size"][1]) / 2
                                      - wall_depth / 2)
        wall_shape = chamfered_rectangle(wall_width, wall_depth,
                                         float(tunnel["chamfer"]), south_only=True)
        add_prism(model, f"{side}_tunnel_wall_barrier", [center[0], wall_center_y],
                  0, wall_shape, wall_height,
                  materials["metal_plate"], yaw)
        highland_end_y = direction * (abs(float(red_main[1]))
                                       + float(highlands["main_size"][1]) / 2)
        landing_depth = float(tunnel["landing_depth"])
        landing_height = highland_top - main_height
        add_box(model, f"{side}_tunnel_highland_landing",
                [center[0], highland_end_y - direction * landing_depth / 2,
                 main_height + landing_height / 2],
                [plate_width, landing_depth, landing_height], materials["metal_plate"])

    # Only the passage on the field-center side of each bridge is a gain zone.
    half_spacing = (float(tunnel["metal_plate_size"][0])
                    + float(tunnel["passage_width_each_side"])) / 2
    marker_size = [tunnel["passage_width_each_side"], tunnel["gap_to_perimeter"],
                   tunnel["marker_height"]]
    red_marker = [red_tunnel_x + half_spacing, red_tunnel_y,
                  float(tunnel["marker_height"]) / 2]
    add_box(model, "red_tunnel_inner_gain_zone", red_marker, marker_size,
            materials["red_supply"], False)
    add_box(model, "blue_tunnel_inner_gain_zone", symmetric_xy(red_marker), marker_size,
            materials["blue_supply"], False)

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
    add_text(camera, "pose", "14 -17 16 0 0.55 2.25")
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
        ("central_control_zone", config["zones"]["central_control"]["center"],
         config["zones"]["central_control"]["size"]),
        ("red_highland_main", highlands["red_main_center"], highlands["main_size"]),
        ("blue_highland_main", symmetric_xy(highlands["red_main_center"]), highlands["main_size"]),
        ("red_highland_guard", highlands["red_guard_center"], highlands["guard_size"]),
        ("blue_highland_guard", symmetric_xy(highlands["red_guard_center"]), highlands["guard_size"]),
        ("red_workbench", config["workbench"]["red_center"], config["workbench"]["size"]),
        ("blue_workbench", symmetric_xy(config["workbench"]["red_center"]), config["workbench"]["size"]),
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

    model_path = args.output_root / "models" / config["model"]["name"] / "model.sdf"
    world_path = args.output_root / "worlds" / f"{config['world']['name']}.world"
    write_xml(generate_model(config), model_path)
    write_xml(generate_world(config), world_path)
    print(f"Generated: {model_path}")
    print(f"Generated: {world_path}")
    print_geometry(config)


if __name__ == "__main__":
    main()
