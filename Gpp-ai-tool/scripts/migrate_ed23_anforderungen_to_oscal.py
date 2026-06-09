#!/usr/bin/env python3
"""One-time migration: gpp_ed23_anforderungen.json -> OSCAL 1.2.2 mapping-collection.

The file used to be a bespoke lookup
(``{"gpp_ed23_anforderungen_map": {control_id: [{id, name, begruendung}, ...]}}``).
This rewrites it in place as a standards-conformant OSCAL Control Mapping document
via ``utils.oscal_mapping.to_oscal_mapping_collection`` — WITHOUT re-running any AI
calls; the existing matches are reused verbatim.

Deterministic + idempotent: re-running on an already-migrated file is a no-op (the
file is left unchanged), because the converter derives all UUIDs with uuid5.

Usage:
    python scripts/migrate_ed23_anforderungen_to_oscal.py [--dry-run] [PATH]

With no PATH, migrates the repo's hilfsdateien/gpp_ed23_anforderungen.json.
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "Gpp-ai-tool", "src"))

from utils.oscal_mapping import MAP_KEY, to_oscal_mapping_collection  # noqa: E402

DEFAULT_PATH = os.path.join(REPO_ROOT, "hilfsdateien", "gpp_ed23_anforderungen.json")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", nargs="?", default=DEFAULT_PATH, help="File to migrate.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing.")
    args = parser.parse_args(argv)

    with open(args.path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "mapping-collection" in data:
        print(f"Already OSCAL (mapping-collection present); nothing to do: {args.path}")
        return 0
    if MAP_KEY not in data:
        print(f"ERROR: neither '{MAP_KEY}' nor 'mapping-collection' found in {args.path}")
        return 1

    per_control = data[MAP_KEY]
    pairs = sum(len(v) for v in per_control.values())
    oscal = to_oscal_mapping_collection(per_control)
    n_maps = len(oscal["mapping-collection"]["mappings"][0]["maps"])
    # Every (control, Anforderung) pair must become exactly one OSCAL map entry.
    assert n_maps == pairs, f"map count {n_maps} != source pair count {pairs}"

    rel = os.path.relpath(args.path, REPO_ROOT)
    if args.dry_run:
        print(f"WOULD convert {len(per_control)} controls / {pairs} pairs -> {n_maps} OSCAL maps in {rel}")
        return 0

    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(oscal, f, ensure_ascii=False, indent=2)  # match utils.save_json_file
    print(f"Converted {len(per_control)} controls / {pairs} pairs -> {n_maps} OSCAL maps in {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
