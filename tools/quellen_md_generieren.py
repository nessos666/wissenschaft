#!/usr/bin/env python3
"""Generiert QUELLEN.md aus dem echten Code (Quelle der Wahrheit: SEARCHER_MAP).

Nutzung:  .venv/bin/python tools/quellen_md_generieren.py
Nach jeder neuen Quelle aufrufen, damit QUELLEN.md nicht veraltet.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from sources.papersearch import ALL_SOURCES, SEARCHER_MAP  # noqa: E402

TITEL = {
    "papersearch": "Vendor-Basis (paper-search-mcp)",
    "extra": "Runde 1 — Chemie/Physik/Preprints/OSF",
    "extra2": "Runde 2 — Medizin/Bio/Labor + CS/Mathe/Bücher",
    "extra3": "Runde 3 — Finance/Regional/Bio-Vertiefung",
    "extra4": "Runde 4 — NCBI- + EBI-Suite (Labor)",
    "extra5": "Runde 5 — Software/Preprints/Bibliotheken",
    "extra6": "Runde 6 — Pakete/Standards/Chemie/Medizin",
    "extra7": "Runde 7 — Förderung/Ökologie/Medien",
    "extra8": "Runde 8 — Naturwissenschaften (Mathe/Bio/Physik/Geo)",
    "extra9": "Runde 9 — EBI Bio/Chemie (PRIDE, InterPro, KEGG …)",
}

gruppen: dict[str, list[str]] = {}
for name, fn in SEARCHER_MAP.items():
    mod = getattr(fn, "__module__", "?").replace("sources.", "").replace("quellen_extra", "extra")
    gruppen.setdefault(mod, []).append(name)

zeilen = [
    f"# Alle Quellen ({len(ALL_SOURCES)} aktiv, key-frei)\n",
    "> Automatisch generiert — **nicht von Hand ändern**.",
    "> Neu erzeugen: `.venv/bin/python tools/quellen_md_generieren.py`\n",
    f"**Gesamt: {len(ALL_SOURCES)} aktive Quellen**\n",
]
for mod in sorted(gruppen, key=lambda m: (m != "papersearch", m)):
    zeilen.append(f"\n## {TITEL.get(mod, mod)} ({len(gruppen[mod])})\n")
    for n in sorted(gruppen[mod]):
        zeilen.append(f"- `{n}`")
    zeilen.append("")

ziel = REPO / "QUELLEN.md"
ziel.write_text("\n".join(zeilen), encoding="utf-8")
print(f"✓ {ziel.name}: {len(ALL_SOURCES)} Quellen in {len(gruppen)} Modulen")
