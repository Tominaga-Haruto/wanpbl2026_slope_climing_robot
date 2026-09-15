"""Strip 'package://' prefix and normalize backslashes to forward slashes in
URDF mesh filename attributes (edited via XML attributes, not raw string
replace).

Usage:
    python fix_mesh_paths.py <urdf_path> [--in-place]
"""
import argparse
import xml.etree.ElementTree as ET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf_path")
    ap.add_argument("--in-place", action="store_true")
    args = ap.parse_args()

    tree = ET.parse(args.urdf_path)
    root = tree.getroot()

    count = 0
    for mesh in root.findall(".//geometry/mesh"):
        old = mesh.get("filename")
        new = old.replace("package://", "").replace("\\", "/")
        if new != old:
            mesh.set("filename", new)
            count += 1
        print(f"  {old}  ->  {new}")

    ET.indent(tree, space="  ")
    out_path = args.urdf_path if args.in_place else args.urdf_path + ".meshfixed"
    tree.write(out_path, xml_declaration=True, encoding="UTF-8")
    print(f"\nChanged {count} mesh filename(s). Written to: {out_path}")


if __name__ == "__main__":
    main()
