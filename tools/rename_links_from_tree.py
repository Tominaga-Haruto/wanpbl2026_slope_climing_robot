"""Rename URDF links mechanically from tree structure (NOT from a hardcoded table).

Rule:
  - root link -> "base"
  - every other link -> lowercased name of the joint whose child it is
    (e.g. child of joint "LR_HR" -> "lr_hr")

Joint names themselves are left untouched (they come from Onshape dof_ mate
names and are trusted). Mesh <geometry><mesh filename=...> is left untouched.

Renaming is done via XML attributes (ElementTree), never raw string
replace, so "part_1" can never accidentally match inside "part_1_2".

Usage:
    python rename_links_from_tree.py <urdf_path> [--in-place]

Without --in-place, writes to <urdf_path>.renamed for inspection first.
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

    links = root.findall("link")
    joints = root.findall("joint")

    link_names = {link.get("name") for link in links}
    child_names = set()
    child_to_joint_name = {}
    for j in joints:
        child = j.find("child").get("link")
        child_names.add(child)
        child_to_joint_name[child] = j.get("name")

    root_candidates = link_names - child_names
    if len(root_candidates) != 1:
        raise SystemExit(f"ERROR: expected exactly 1 root link, found {root_candidates}")
    root_link_name = next(iter(root_candidates))

    mapping = {root_link_name: "base"}
    for child, joint_name in child_to_joint_name.items():
        mapping[child] = joint_name.lower()

    print("--- Rename mapping (old -> new) ---")
    for old, new in mapping.items():
        print(f"  {old} -> {new}")

    # Sanity: no collisions
    new_names = list(mapping.values())
    if len(new_names) != len(set(new_names)):
        raise SystemExit("ERROR: rename mapping produces duplicate names, aborting")

    for link in links:
        old = link.get("name")
        link.set("name", mapping[old])

    for j in joints:
        parent_el = j.find("parent")
        child_el = j.find("child")
        parent_el.set("link", mapping[parent_el.get("link")])
        child_el.set("link", mapping[child_el.get("link")])

    ET.indent(tree, space="  ")
    out_path = args.urdf_path if args.in_place else args.urdf_path + ".renamed"
    tree.write(out_path, xml_declaration=True, encoding="unicode" if False else "UTF-8")
    print(f"\nWritten to: {out_path}")


if __name__ == "__main__":
    main()
