#!/usr/bin/env python3
"""One-time migration: maturity-statement props -> prose + nested parts (issue 3.1).

Older enhanced profiles encoded each maturity level as a `statement` part whose `prose`
was the (duplicated) original control description, with the real per-level text stored in
custom props `statement` / `guidance` / `assessment-method`. This script rewrites every such
part in place to the new, OSCAL-idiomatic shape produced by
`build_oscal_maturity_statements`:

    part.prose            <- the props "statement" value (the real per-level text)
    nested guidance part  <- the props "guidance" value
    nested assessment part <- the props "assessment-method" value
    props                  <- classification props (control_class, phase, effective_on_*)
                              plus the level `label`; the statement/guidance/assessment
                              props are removed.

The transform is deterministic (no AI) and idempotent: parts already in the new shape (no
`statement` prop) are left untouched. Targets the generated profile directories.

Usage:
    python scripts/migrate_maturity_parts_to_prose.py [--dry-run] [PATH ...]

With no PATH, migrates the default generated directories:
    ED23-Baustein-profile/DE/  and  Zielobjektkategorien/profile/process/
"""
import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DIRS = [
    os.path.join(REPO_ROOT, "ED23-Baustein-profile", "DE"),
    os.path.join(REPO_ROOT, "Zielobjektkategorien", "profile", "process"),
]

# Props that carried prose in the old shape and must NOT survive as props.
_PROSE_PROPS = {"statement", "guidance", "assessment-method"}


def _migrate_part(part: dict) -> bool:
    """Migrate a single maturity `statement` part in place. Returns True if changed."""
    props = part.get("props") or []
    prop_map = {p.get("name"): p.get("value") for p in props if isinstance(p, dict)}

    # Only old-shape maturity parts carry a "statement" prop. Skip anything else
    # (already migrated, or a non-maturity part).
    if "statement" not in prop_map:
        return False

    statement_text = prop_map.get("statement") or part.get("prose") or ""
    guidance_text = prop_map.get("guidance") or ""
    assessment_text = prop_map.get("assessment-method") or ""

    # Keep classification + label props; drop the prose-bearing ones.
    part["props"] = [
        p for p in props
        if isinstance(p, dict) and p.get("name") not in _PROSE_PROPS
    ]

    part["prose"] = statement_text

    part_id = part.get("id", "")
    nested = []
    if guidance_text:
        nested.append({"id": f"{part_id}_gdn", "name": "guidance", "prose": guidance_text})
    if assessment_text:
        nested.append({"id": f"{part_id}_asm", "name": "assessment", "prose": assessment_text})

    # Preserve any pre-existing nested parts that are not our guidance/assessment.
    existing = [
        p for p in (part.get("parts") or [])
        if isinstance(p, dict) and p.get("name") not in ("guidance", "assessment")
    ]
    combined = nested + existing
    if combined:
        part["parts"] = combined
    elif "parts" in part:
        del part["parts"]

    return True


def migrate_profile(data: dict) -> int:
    """Walk a profile's modify.alters[].adds[].parts and migrate each. Returns count changed."""
    changed = 0
    alters = (((data or {}).get("profile") or {}).get("modify") or {}).get("alters") or []
    for alter in alters:
        for add in (alter.get("adds") or []):
            for part in (add.get("parts") or []):
                if isinstance(part, dict) and _migrate_part(part):
                    changed += 1
    return changed


def iter_json_files(paths):
    for path in paths:
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                if name.endswith(".json"):
                    yield os.path.join(path, name)
        elif os.path.isfile(path) and path.endswith(".json"):
            yield path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Files or directories to migrate.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing.")
    args = parser.parse_args(argv)

    targets = args.paths or DEFAULT_DIRS
    files = list(iter_json_files(targets))
    if not files:
        print("No JSON files found in:", ", ".join(targets))
        return 1

    total_files, total_parts = 0, 0
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"SKIP (cannot read) {fpath}: {e}")
            continue

        changed = migrate_profile(data)
        if changed:
            total_files += 1
            total_parts += changed
            if args.dry_run:
                print(f"WOULD migrate {changed:3d} parts in {os.path.relpath(fpath, REPO_ROOT)}")
            else:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"migrated {changed:3d} parts in {os.path.relpath(fpath, REPO_ROOT)}")

    verb = "would migrate" if args.dry_run else "migrated"
    print(f"\nDone: {verb} {total_parts} parts across {total_files} files "
          f"(scanned {len(files)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
