#!/usr/bin/env python3
"""One-time migration: drop effective_on_* props, normalize classification-prop ns.

The BSI Stand-der-Technik-Bibliothek now carries authoritative Schutzziel-impact props
on every control (confidentiality / integrity / availability / authenticity, values 0-2,
ns .../documentation/namespaces/security_targets.csv). Our AI-generated per-maturity
props `effective_on_c/i/a` duplicated that information and are removed; consumers read
the BSI props from the imported catalog instead.

This script rewrites every maturity `statement` part in the generated enhanced profiles:

    props effective_on_c / effective_on_i / effective_on_a  -> removed
    props control_class / phase                             -> ns set to
                                                               GPP_ENHANCEMENT_PROPS_NS
                                                               (fixes the old hardcoded
                                                               BSI ns in process profiles)

The transform is deterministic (no AI) and idempotent. Targets the generated profile
directories.

Usage:
    python scripts/migrate_remove_effective_on_props.py [--dry-run] [PATH ...]

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

sys.path.insert(0, os.path.join(REPO_ROOT, "Gpp-ai-tool", "src"))
from constants import GPP_ENHANCEMENT_PROPS_NS  # noqa: E402

_DROP_PROPS = {"effective_on_c", "effective_on_i", "effective_on_a"}
_GPP_NS_PROPS = {"control_class", "phase"}


def _migrate_part(part: dict) -> bool:
    """Migrate a single part's props in place. Returns True if changed."""
    props = part.get("props")
    if not props:
        return False

    changed = False
    kept = []
    for p in props:
        if not isinstance(p, dict):
            kept.append(p)
            continue
        name = p.get("name")
        if name in _DROP_PROPS:
            changed = True
            continue
        if name in _GPP_NS_PROPS and p.get("ns") != GPP_ENHANCEMENT_PROPS_NS:
            p["ns"] = GPP_ENHANCEMENT_PROPS_NS
            changed = True
        kept.append(p)

    if changed:
        part["props"] = kept
    return changed


def migrate_profile(data: dict) -> int:
    """Walk modify.alters[].adds[].parts (incl. nested) and migrate each. Returns count changed."""
    changed = 0

    def walk_parts(parts):
        nonlocal changed
        for part in parts or []:
            if not isinstance(part, dict):
                continue
            if _migrate_part(part):
                changed += 1
            walk_parts(part.get("parts"))

    alters = (((data or {}).get("profile") or {}).get("modify") or {}).get("alters") or []
    for alter in alters:
        for add in (alter.get("adds") or []):
            walk_parts(add.get("parts"))
    return changed


def iter_json_files(paths):
    for path in paths:
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                if name.endswith("_enhanced.json"):
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
