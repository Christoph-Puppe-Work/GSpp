#!/usr/bin/env python3
"""pin_profile_imports.py -- v1.0.0

Stellt OSCAL-Profile vom direkten Branch-Import auf das Pin-Muster um
(Handbuch Kapitel 3.13/3.14, Skill gs-plusplus-katalogarbeit Grundregel 8):

  vorher:  import.href = https://raw.githubusercontent.com/.../refs/heads/main/...
  nachher: import.href = "#<resource-uuid>"
           back-matter.resource.rlink = URL mit Commit-SHA + SHA-256-Hash

Eigenschaften:
- Idempotent: Fragment-Importe ("#...") werden uebersprungen.
- Deterministisch: Resource-UUID = uuid5(NAMESPACE_URL, gepinnte URL),
  d.h. gleiche Quelle ergibt in allen Profilen dieselbe UUID.
- Ein Download je Ziel-URL (Cache), Hash wird lokal berechnet.
- Nur stdlib, kein Build-Schritt.

Aufruf:
  python3 pin_profile_imports.py <verzeichnis> [--commit SHA] [--dry-run]

Erfolgskriterium (selbstpruefend): Nach dem Lauf laedt jedes geaenderte
Profil als JSON, jeder Import ist ein Fragment, jede referenzierte
Resource existiert und traegt genau einen SHA-256-Hash, und der Hash
entspricht dem heruntergeladenen Inhalt der gepinnten URL.
"""

import argparse
import hashlib
import json
import sys
import urllib.request
import uuid
from pathlib import Path

BRANCH_MARKERS = ("/refs/heads/main/", "/main/")
GITHUB_API = "https://api.github.com/repos/{repo}/commits/{ref}"
UA = {"User-Agent": "pin-profile-imports/1.0"}


def resolve_commit(url: str, override: str | None) -> str:
    """Ermittelt den aktuellen Commit-SHA des Branches.

    Erst GitHub-API, bei 403 (unauthentifiziertes Rate-Limit) Fallback
    auf `git ls-remote`; beides fehlgeschlagen -> --commit verwenden.
    """
    if override:
        return override
    # raw.githubusercontent.com/<owner>/<repo>/refs/heads/<branch>/<pfad>
    parts = url.split("raw.githubusercontent.com/", 1)[1].split("/")
    repo = "/".join(parts[0:2])
    try:
        req = urllib.request.Request(
            GITHUB_API.format(repo=repo, ref="main"), headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["sha"]
    except urllib.error.HTTPError:
        import subprocess
        out = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{repo}.git",
             "refs/heads/main"],
            capture_output=True, text=True, timeout=60, check=True)
        return out.stdout.split()[0]


def pin_url(url: str, sha: str) -> str:
    for marker in BRANCH_MARKERS:
        if marker in url:
            return url.replace(marker, f"/{sha}/", 1)
    raise ValueError(f"Kein Branch-Marker in URL: {url}")


def fetch_sha256(url: str, cache: dict) -> str:
    if url not in cache:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        json.loads(data)  # Ziel muss valides JSON sein, sonst Abbruch
        cache[url] = hashlib.sha256(data).hexdigest()
        print(f"  Quelle geladen: {url.rsplit('/', 1)[-1]} "
              f"({len(data)} Bytes, sha256 {cache[url][:12]}...)")
    return cache[url]


def migrate_profile(path: Path, sha: str, cache: dict, dry: bool) -> str:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "kein-json"
    profile = doc.get("profile")
    if not profile:
        return "kein-profil"

    imports = profile.get("imports", [])
    todo = [i for i in imports if i.get("href", "").startswith("http")]
    if not todo:
        return "bereits-gepinnt" if imports else "keine-importe"

    resources = profile.setdefault("back-matter", {}).setdefault("resources", [])
    known = {r["uuid"] for r in resources}

    for imp in todo:
        pinned = pin_url(imp["href"], sha)
        digest = fetch_sha256(pinned, cache)
        res_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, pinned))
        if res_uuid not in known:
            from urllib.parse import unquote
            resources.append({
                "uuid": res_uuid,
                "title": f"{unquote(pinned.rsplit('/', 1)[-1])} @ {sha[:12]}",
                "rlinks": [{
                    "href": pinned,
                    "hashes": [{"algorithm": "SHA-256", "value": digest}],
                }],
            })
            known.add(res_uuid)
        imp["href"] = f"#{res_uuid}"

    if not dry:
        path.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return "gepinnt"


def verify(path: Path, cache: dict) -> bool:
    """Selbstpruefung gegen das Erfolgskriterium aus dem Docstring."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    profile = doc["profile"]
    res = {r["uuid"]: r for r in profile.get("back-matter", {}).get("resources", [])}
    for imp in profile.get("imports", []):
        href = imp.get("href", "")
        if not href.startswith("#"):
            return False
        r = res.get(href[1:])
        if not r:
            return False
        rlink = r["rlinks"][0]
        hashes = rlink.get("hashes", [])
        if len(hashes) != 1 or hashes[0]["algorithm"] != "SHA-256":
            return False
        if cache.get(rlink["href"]) != hashes[0]["value"]:
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path, help="Wurzelverzeichnis mit Profilen")
    ap.add_argument("--commit", help="Commit-SHA statt API-Abfrage von main")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen")
    args = ap.parse_args()

    files = sorted(args.root.rglob("*.json"))
    if not files:
        print(f"Keine JSON-Dateien unter {args.root}", file=sys.stderr)
        return 1

    # Commit-SHA einmal ermitteln, anhand der ersten Branch-URL im Bestand
    sample = None
    for f in files:
        try:
            p = json.loads(f.read_text(encoding="utf-8")).get("profile", {})
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for i in p.get("imports", []):
            if i.get("href", "").startswith("http"):
                sample = i["href"]
                break
        if sample:
            break
    if not sample:
        print("Nichts zu tun: kein Profil mit http-Import gefunden.")
        return 0

    sha = resolve_commit(sample, args.commit)
    print(f"Pin-Ziel: Commit {sha}{' (dry-run)' if args.dry_run else ''}\n")

    cache: dict = {}
    stats: dict = {}
    changed: list = []
    for f in files:
        state = migrate_profile(f, sha, cache, args.dry_run)
        stats[state] = stats.get(state, 0) + 1
        if state == "gepinnt":
            changed.append(f)

    print("\nErgebnis:", ", ".join(f"{k}: {v}" for k, v in sorted(stats.items())))

    if not args.dry_run and changed:
        bad = [f for f in changed if not verify(f, cache)]
        if bad:
            print(f"FEHLER: Selbstpruefung fehlgeschlagen fuer {len(bad)} "
                  f"Datei(en), z. B. {bad[0]}", file=sys.stderr)
            return 1
        print(f"Selbstpruefung: {len(changed)} Profile verifiziert "
              f"(Fragment-Import, Resource vorhanden, SHA-256 korrekt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
