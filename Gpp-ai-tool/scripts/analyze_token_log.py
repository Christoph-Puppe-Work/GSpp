#!/usr/bin/env python3
"""Wertet die Token-Logzeilen von stage_ed23_anforderungen aus.

Sucht in einem Logfile (oder stdin) nach den vom AiClient erzeugten Zeilen der Form

    [ED23Abgleich-GC.10.1] tokens: prompt=140803 cached(saved)=140402 output=373

und fasst sie zusammen: Anzahl Requests, Summe Input-/Cache-/Output-Tokens, der wirklich
neu pro Control gesendete Anteil sowie eine grobe Kostenschätzung (mit/ohne Cache).

Preis-Defaults: Gemini 3 Flash (Standard, Global) laut Vertex-AI-/Agent-Platform-Preisliste,
Stand Juni 2026 — Input $1.50/1M, Output $9.00/1M, Cached Input $0.15/1M (= 10 % des Inputs,
also 90 % Rabatt). Cache-Storage (~$1/1M Tokens/Stunde) ist optional über --cache-tokens /
--cache-hours / --storage-price zuschaltbar. Preise bei Modell-/Tier-/Regionswechsel anpassen.

Beispiele:
    python scripts/analyze_token_log.py run_local.log
    cat run_local.log | python scripts/analyze_token_log.py
    # inkl. Storage: 140k-Korpus, 4h TTL, $1/1M/h
    python scripts/analyze_token_log.py run_local.log --cache-tokens 140402 --cache-hours 4
"""

import argparse
import re
import sys
from typing import List, Tuple

# Erfasst sowohl die Cache-aktive Variante `cached(saved)=` als auch die Debug-Variante `cached=`.
LINE_RE = re.compile(
    r"\[([^\]]+)\]\s+tokens:\s*prompt=(\d+)\s+cached(?:\(saved\))?=(\d+)\s+output=(\d+)"
)


def parse(lines) -> List[Tuple[str, int, int, int]]:
    """Liefert pro passender Zeile (label, prompt, cached, output)."""
    rows = []
    for line in lines:
        m = LINE_RE.search(line)
        if m:
            rows.append((m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))))
    return rows


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")  # Tausenderpunkte (de)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logfile", nargs="?", help="Pfad zum Logfile (default: stdin)")
    # Preise pro 1 Mio. Tokens (USD). Defaults: Gemini 3 Flash (Standard, Global), Stand 06/2026.
    ap.add_argument("--in-price", type=float, default=1.50, help="Input-Preis pro 1M Tokens (USD)")
    ap.add_argument("--cached-price", type=float, default=0.15, help="Cached-Input-Preis pro 1M Tokens (USD)")
    ap.add_argument("--out-price", type=float, default=9.00, help="Output-Preis pro 1M Tokens (USD)")
    # Optionale Cache-Storage-Kosten (nur berücksichtigt, wenn --cache-tokens > 0).
    ap.add_argument("--cache-tokens", type=int, default=0, help="Größe des Korpus im Cache (Tokens)")
    ap.add_argument("--cache-hours", type=float, default=0.0, help="Lebensdauer des Caches in Stunden (TTL)")
    ap.add_argument("--storage-price", type=float, default=1.0, help="Cache-Storage-Preis pro 1M Tokens/Stunde (USD)")
    ap.add_argument("--top", type=int, default=5, help="Anzahl teuerster Controls in der Liste")
    args = ap.parse_args()

    if args.logfile:
        with open(args.logfile, "r", encoding="utf-8", errors="replace") as f:
            rows = parse(f)
    else:
        rows = parse(sys.stdin)

    if not rows:
        print("Keine passenden Token-Zeilen gefunden.", file=sys.stderr)
        return 1

    n = len(rows)
    sum_prompt = sum(r[1] for r in rows)
    sum_cached = sum(r[2] for r in rows)
    sum_output = sum(r[3] for r in rows)
    sum_fresh = sum_prompt - sum_cached  # tatsächlich neu gesendete Input-Tokens
    hit_ratio = sum_cached / sum_prompt if sum_prompt else 0.0

    M = 1_000_000
    # Kosten MIT Cache: frischer Input + Cache-Tokens (vergünstigt) + Output.
    cost_cached = (sum_fresh * args.in_price + sum_cached * args.cached_price + sum_output * args.out_price) / M
    # Optionale Cache-Storage-Kosten (einmal pro Cache-Lebensdauer, nicht pro Request).
    storage_cost = (args.cache_tokens * args.cache_hours * args.storage_price) / M
    cost_cached += storage_cost
    # Kosten OHNE Cache: der gesamte Input zum vollen Preis (jede Anfrage trägt den Korpus).
    cost_nocache = (sum_prompt * args.in_price + sum_output * args.out_price) / M
    savings = cost_nocache - cost_cached

    print("=" * 60)
    print("Token-Auswertung stage_ed23_anforderungen")
    print("=" * 60)
    print(f"Requests (Controls)        : {fmt(n)}")
    print(f"Input gesamt (prompt)      : {fmt(sum_prompt)} Tokens")
    print(f"  davon aus Cache (saved)  : {fmt(sum_cached)} Tokens  ({hit_ratio*100:.1f} %)")
    print(f"  davon neu pro Control    : {fmt(sum_fresh)} Tokens  ({fmt(sum_fresh/n)} Ø/Control)")
    print(f"Output gesamt              : {fmt(sum_output)} Tokens  ({fmt(sum_output/n)} Ø/Control)")
    print("-" * 60)
    print(f"Kostenmodell (USD / 1M): in={args.in_price}  cached={args.cached_price}  out={args.out_price}")
    if storage_cost:
        print(f"Cache-Storage              : ${storage_cost:,.4f}  "
              f"({fmt(args.cache_tokens)} Tok x {args.cache_hours} h x ${args.storage_price}/1M/h)")
    print(f"Kosten MIT Cache           : ${cost_cached:,.4f}")
    print(f"Kosten OHNE Cache (hypoth.): ${cost_nocache:,.4f}")
    if cost_nocache:
        print(f"Ersparnis durch Cache      : ${savings:,.4f}  ({savings/cost_nocache*100:.1f} %)")

    if args.top > 0:
        print("-" * 60)
        print(f"Top {args.top} Controls nach Output-Tokens:")
        for label, p, c, o in sorted(rows, key=lambda r: r[3], reverse=True)[: args.top]:
            print(f"  {label:<28} output={fmt(o):>8}  fresh_in={fmt(p - c):>6}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
